# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""A collection of hooks to process IssueTracker related events."""

import collections
import itertools
import logging
import urlparse
import html2text

import sqlalchemy as sa

from ggrc import access_control
from ggrc import db
from ggrc import utils
from ggrc import settings
from ggrc.models import all_models
from ggrc.integrations import issues
from ggrc.integrations import integrations_errors
from ggrc.models import exceptions
from ggrc.services import signals
from ggrc.utils import referenced_objects


logger = logging.getLogger(__name__)


_ISSUE_URL_TMPL = settings.ISSUE_TRACKER_BUG_URL_TMPL or 'http://issue/%s'

_ISSUE_TRACKER_ENABLED = bool(settings.ISSUE_TRACKER_ENABLED)
if not _ISSUE_TRACKER_ENABLED:
  logger.debug('IssueTracker integration is disabled.')

_ASSESSMENT_MODEL_NAME = 'Assessment'
_ASSESSMENT_TMPL_MODEL_NAME = 'AssessmentTemplate'
_AUDIT_MODEL_NAME = 'Audit'

_SUPPORTED_MODEL_NAMES = {
    _ASSESSMENT_TMPL_MODEL_NAME,
    _AUDIT_MODEL_NAME,
}

# mapping of model field name to API property name
_ISSUE_TRACKER_UPDATE_FIELDS = (
    ('title', 'title'),
    ('issue_priority', 'priority'),
    ('issue_severity', 'severity'),
    ('component_id', 'component_id'),
)

_INITIAL_COMMENT_TMPL = (
    'This bug was auto-generated to track a GGRC assessment (a.k.a PBC Item). '
    'Use the following link to find the assessment - %s.'
)

_STATUS_CHANGE_COMMENT_TMPL = (
    'The status of this bug was automatically synced to reflect current GGRC '
    'assessment status. Current status of related GGRC Assessment is %s. '
    'Use the following to link to get information from the GGRC Assessment '
    'on why the status may have changed. '
    'Link - %s'
)

_COMMENT_TMPL = (
    'A new comment is added by %s to the Assessment: %s. '
    'Use the following to link to get more information from the '
    'GGRC Assessment. Link - %s'
)

_ARCHIVED_TMPL = (
    'Assessment has been archived. Changes to this GGRC Assessment will '
    'not be tracked within this bug until Assessment is unlocked.'
)

_UNARCHIVED_TMPL = (
    'Assessment has been unarchived. Changes to this GGRC Assessment will '
    'be tracked within this bug.'
)

_ENABLED_TMPL = (
    'Changes to this GGRC Assessment will be tracked within this bug.'
)

_DISABLED_TMPL = (
    'Changes to this GGRC Assessment will no longer be '
    'tracked within this bug.'
)


# Status transitions map for assessment without verifier.
_NO_VERIFIER_STATUSES = {
    # (from_status, to_status): 'issue_tracker_status'
    ('Not Started', 'Completed'): 'VERIFIED',
    ('In Progress', 'Completed'): 'VERIFIED',

    ('Completed', 'In Progress'): 'ASSIGNED',
    ('Deprecated', 'In Progress'): 'ASSIGNED',

    ('Completed', 'Not Started'): 'ASSIGNED',
    ('Deprecated', 'Not Started'): 'ASSIGNED',

    ('Not Started', 'Deprecated'): 'OBSOLETE',
    ('In Progress', 'Deprecated'): 'OBSOLETE',
    ('Completed', 'Deprecated'): 'OBSOLETE',
}

# Status transitions map for assessment with verifier.
_VERIFIER_STATUSES = {
    # (from_status, to_status, verified): 'issue_tracker_status'
    # When verified is True 'Completed' means 'Completed and Verified'.

    # State: FIXED
    ('Not Started', 'In Review', False): 'FIXED',
    ('In Progress', 'In Review', False): 'FIXED',
    ('Rework Needed', 'In Review', False): 'FIXED',
    ('Completed', 'In Review', True): 'FIXED',
    ('Deprecated', 'In Review', False): 'FIXED',

    # State: ASSIGNED
    ('In Review', 'In Progress', False): 'ASSIGNED',
    # if gets from Completed and Verified to In Progress, can not be verified
    ('Completed', 'In Progress', False): 'ASSIGNED',
    ('Deprecated', 'In Progress', False): 'ASSIGNED',

    # State: ASSIGNED
    ('In Review', 'Rework Needed', False): 'ASSIGNED',
    ('Completed', 'Rework Needed', True): 'ASSIGNED',
    ('Deprecated', 'Rework Needed', False): 'ASSIGNED',

    # State: FIXED (Verified)
    ('Not Started', 'Completed', True): 'VERIFIED',
    ('In Progress', 'Completed', True): 'VERIFIED',
    ('In Review', 'Completed', True): 'VERIFIED',
    ('Rework Needed', 'Completed', True): 'VERIFIED',
    ('Deprecated', 'Completed', True): 'VERIFIED',

    # State: ASSIGNED
    ('In Review', 'Not Started', False): 'ASSIGNED',
    ('Rework Needed', 'Not Started', False): 'ASSIGNED',
    ('Completed', 'Not Started', True): 'ASSIGNED',
    ('Deprecated', 'Not Started', False): 'ASSIGNED',

    # State: WON'T FIX (OBSOLETE)
    ('Not Started', 'Deprecated', False): 'OBSOLETE',
    ('In Progress', 'Deprecated', False): 'OBSOLETE',
    ('In Review', 'Deprecated', False): 'OBSOLETE',
    ('Rework Needed', 'Deprecated', False): 'OBSOLETE',
    ('Completed', 'Deprecated', True): 'OBSOLETE',
}


def _handle_assessment_tmpl_post(sender, objects=None, sources=None):
  """Handles create event to AssessmentTemplate model."""
  del sender  # Unused

  for src in sources:
    _validate_issue_tracker_info(src.get('issue_tracker') or {})

  db.session.flush()
  template_ids = {
      obj.id for obj in objects
  }

  if not template_ids:
    return

  # TODO(anushovan): use joined query to fetch audits or even
  #   issuetracker_issues with one query.
  audit_map = {
      r.destination_id: r.source_id
      for r in all_models.Relationship.query.filter(
          all_models.Relationship.source_type == 'Audit',
          all_models.Relationship.destination_type == 'AssessmentTemplate',
          all_models.Relationship.destination_id.in_(template_ids)).all()
  }

  if not audit_map:
    return

  audits = {
      a.id: a
      for a in all_models.Audit.query.filter(
          all_models.Audit.id.in_(audit_map.values())).all()
  }

  for obj, src in itertools.izip(objects, sources):
    audit_id = audit_map.get(obj.id)
    audit = audits.get(audit_id) if audit_id else None
    if not audit or not _is_issue_tracker_enabled(audit=audit):
      issue_tracker_info = {
          'enabled': False,
      }
    else:
      issue_tracker_info = src.get('issue_tracker')

    if not issue_tracker_info:
      continue
    all_models.IssuetrackerIssue.create_or_update_from_dict(
        obj, issue_tracker_info)


def _handle_assessment_tmpl_put(sender, obj=None, src=None, service=None,
                                initial_state=None):
  """Handles update event to AssessmentTemplate model."""
  del sender, service, initial_state  # Unused

  issue_tracker_info = src.get('issue_tracker') or {}
  _validate_issue_tracker_info(issue_tracker_info)

  audit = all_models.Audit.query.join(
      all_models.Relationship,
      all_models.Relationship.source_id == all_models.Audit.id,
  ).filter(
      all_models.Relationship.source_type == 'Audit',
      all_models.Relationship.destination_type == 'AssessmentTemplate',
      all_models.Relationship.destination_id == obj.id
  ).first()

  if not audit or not _is_issue_tracker_enabled(audit=audit):
    issue_tracker_info = {
        'enabled': False,
    }

  if issue_tracker_info:
    all_models.IssuetrackerIssue.create_or_update_from_dict(
        obj, issue_tracker_info)


def _handle_deleted_after_commit(sender, obj=None, service=None, event=None):
  """Handles IssueTracker information during delete event."""
  del sender, service, event  # Unused

  model_name = obj.__class__.__name__
  if model_name not in _SUPPORTED_MODEL_NAMES:
    return

  issue_obj = all_models.IssuetrackerIssue.get_issue(model_name, obj.id)
  if issue_obj:
    db.session.delete(issue_obj)


def _handle_audit_post(sender, objects=None, sources=None):
  """Handles creating issue tracker related info."""
  del sender  # Unused
  for obj, src in itertools.izip(objects, sources):
    issue_tracker_info = src.get('issue_tracker')
    if not issue_tracker_info:
      continue
    _validate_issue_tracker_info(issue_tracker_info)
    all_models.IssuetrackerIssue.create_or_update_from_dict(
        obj, issue_tracker_info)


def _handle_audit_put(sender, obj=None, src=None, service=None):
  """Handles updating issue tracker related info."""
  del sender, service  # Unused
  issue_tracker_info = src.get('issue_tracker')
  if issue_tracker_info:
    _validate_issue_tracker_info(issue_tracker_info)
    all_models.IssuetrackerIssue.create_or_update_from_dict(
        obj, issue_tracker_info)


def _handle_audit_put_after_commit(sender, obj=None, **kwargs):
  """Handles updating issue tracker related info."""
  del sender  # Unused

  initial_state = kwargs.get('initial_state')
  if not initial_state:
    logger.debug(
        'Initial state of an Audit is not provided, '
        'skipping IssueTracker update.')
    return

  if (obj.archived == initial_state.archived or
          not obj.issue_tracker.get('enabled', False)):
    return

  start_update_issue_job(
      obj.id,
      _ARCHIVED_TMPL if obj.archived else _UNARCHIVED_TMPL)


def _handle_issuetracker(sender, obj=None, src=None, **kwargs):
  """Handles IssueTracker information during assessment update event."""
  del sender  # Unused

  if not _is_issue_tracker_enabled(audit=obj.audit):
    # Skip updating issue and info if feature is disabled on Audit level.
    return

  issue_obj = all_models.IssuetrackerIssue.get_issue(
      _ASSESSMENT_MODEL_NAME, obj.id)

  initial_info = issue_obj.to_dict(
      include_issue=True,
      include_private=True) if issue_obj is not None else {}
  issue_tracker_info = dict(initial_info, **(src.get('issue_tracker') or {}))

  if issue_tracker_info.get('enabled'):

    issue_id = issue_tracker_info.get('issue_id')

    if not issue_id:
      # If assessment initially was created with disabled IssueTracker.
      _create_issuetracker_info(obj, issue_tracker_info)
      return

    _, issue_tracker_info['cc_list'] = _collect_issue_emails(obj)

  else:
    issue_tracker_info['enabled'] = False

  initial_assessment = kwargs.pop('initial_state', None)
  try:
    _update_issuetracker_issue(
        obj, issue_tracker_info, initial_assessment, initial_info, src)
  except integrations_errors.Error as error:
    if error.status == 429:
      logger.error(
          'The request updating ticket ID=%s for assessment ID=%d was '
          'rate limited: %s', issue_id, obj.id, error)
    else:
      logger.error(
          'Unable to update a ticket ID=%s while updating '
          'assessment ID=%d: %s', issue_id, obj.id, error)
      issue_tracker_info = {
          'enabled': False,
      }
    obj.add_warning('issue_tracker', 'Unable to update a ticket.')

  _update_issuetracker_info(obj, issue_tracker_info)


def _handle_assessment_deleted(sender, obj=None, service=None):
  """Handles assessment delete event."""
  del sender, service  # Unused

  issue_obj = all_models.IssuetrackerIssue.get_issue(
      _ASSESSMENT_MODEL_NAME, obj.id)

  if issue_obj:
    if (issue_obj.enabled and
            issue_obj.issue_id and
            _is_issue_tracker_enabled(audit=obj.audit)):
      issue_params = {
          'status': 'OBSOLETE',
          'comment': (
              'Assessment has been deleted. Changes to this GGRC '
              'Assessment will no longer be tracked within this bug.'
          ),
      }
      try:
        issues.Client().update_issue(issue_obj.issue_id, issue_params)
      except integrations_errors.Error as error:
        logger.error('Unable to update a ticket ID=%s while deleting'
                     ' assessment ID=%d: %s',
                     issue_obj.issue_id, obj.id, error)
    db.session.delete(issue_obj)


def init_hook():
  """Initializes hooks."""

  signals.Restful.collection_posted.connect(
      _handle_assessment_tmpl_post, sender=all_models.AssessmentTemplate)

  signals.Restful.model_put.connect(
      _handle_assessment_tmpl_put, sender=all_models.AssessmentTemplate)

  signals.Restful.model_deleted_after_commit.connect(
      _handle_deleted_after_commit, sender=all_models.Audit)
  signals.Restful.model_deleted_after_commit.connect(
      _handle_deleted_after_commit, sender=all_models.AssessmentTemplate)

  signals.Restful.collection_posted.connect(
      _handle_audit_post, sender=all_models.Audit)

  signals.Restful.model_put.connect(
      _handle_audit_put, sender=all_models.Audit)

  signals.Restful.model_put_after_commit.connect(
      _handle_audit_put_after_commit, sender=all_models.Audit)

  signals.Restful.model_put_before_commit.connect(
      _handle_issuetracker, sender=all_models.Assessment)

  signals.Restful.model_deleted.connect(
      _handle_assessment_deleted, sender=all_models.Assessment)


def start_update_issue_job(audit_id, message):
  """Creates background job for handling IssueTracker issue update."""
  from ggrc import views
  views.start_update_audit_issues(audit_id, message)


def handle_assessment_create(assessment, src):
  """Handles issue tracker related data."""
  # Get issue tracker data from request.
  info = src.get('issue_tracker') or {}

  if not info:
    # Check assessment template for issue tracker data.
    template = referenced_objects.get(
        src.get('template', {}).get('type'),
        src.get('template', {}).get('id'),
    )
    if template:
      info = template.issue_tracker

  if not info:
    # Check audit for issue tracker data.
    audit = referenced_objects.get(
        src.get('audit', {}).get('type'),
        src.get('audit', {}).get('id'),
    )
    if audit:
      info = audit.issue_tracker

  _create_issuetracker_info(assessment, info)


def _validate_issue_tracker_info(info):
  """Validates that component ID and hotlist ID are integers."""
  component_id = info.get('component_id')
  if component_id:
    try:
      int(component_id)
    except (TypeError, ValueError):
      raise exceptions.ValidationError('Component ID must be a number.')

  hotlist_id = info.get('hotlist_id')
  if hotlist_id:
    try:
      int(hotlist_id)
    except (TypeError, ValueError):
      raise exceptions.ValidationError('Hotlist ID must be a number.')


def _normalize_issue_tracker_info(info):
  """Insures that component ID and hotlist ID are integers."""
  # TODO(anushovan): remove data type casting once integration service
  #   supports strings for following properties.
  component_id = info.get('component_id')
  if component_id:
    try:
      info['component_id'] = int(component_id)
    except (TypeError, ValueError):
      raise exceptions.ValidationError('Component ID must be a number.')

  hotlist_id = info.get('hotlist_id')
  if hotlist_id:
    try:
      info['hotlist_id'] = int(hotlist_id)
    except (TypeError, ValueError):
      raise exceptions.ValidationError('Hotlist ID must be a number.')


def _handle_basic_props(issue_tracker_info, initial_info):
  """Handles updates to basic issue tracker properties."""
  issue_params = {}
  for name, api_name in _ISSUE_TRACKER_UPDATE_FIELDS:
    if name not in issue_tracker_info:
      continue
    value = issue_tracker_info[name]
    if value != initial_info.get(name):
      issue_params[api_name] = value
  return issue_params


def _get_roles(assessment):
  """Returns emails associated with an assessment grouped by role.

  Args:
    assessment: An instance of Assessment model.

  Returns:
    A dict of {'role name': {set of emails}}.
  """
  all_roles = collections.defaultdict(set)

  ac_list = access_control.list.AccessControlList
  ac_role = access_control.role.AccessControlRole
  query = db.session.query(
      ac_list.person_id,
      ac_role.name,
      all_models.Person.email
  ).join(
      ac_role,
      ac_role.id == ac_list.ac_role_id
  ).join(
      all_models.Person,
      all_models.Person.id == ac_list.person_id
  ).filter(
      ac_list.object_type == _ASSESSMENT_MODEL_NAME,
      ac_list.object_id == assessment.id,
      ac_role.internal == sa.sql.false(),
  )
  for row in query.all():
    # row = (person_id, role_name, email)
    all_roles[row[1]].add(row[2])

  return all_roles


def _collect_issue_emails(assessment):
  """Returns emails related to given assessment.

  The lexicographical first Assignee is used for assignee_email.
  Every other Assignee is used in related_people_emails.
  Creators, Verifiers, Primary Contacts, Secondary Contacts
  and any other Assessment custom roles should NOT be used in
  related_people_emails.

  Args:
    assessment: An instance of Assessment model.

  Returns:
    A tuple of (assignee_email, [related_people_emails])
  """
  cc_list = _get_roles(assessment).get('Assignees')
  cc_list = sorted(cc_list) if cc_list else []
  assignee_email = cc_list.pop(0) if cc_list else None
  return assignee_email, cc_list


def _get_assessment_url(assessment):
  """Returns string URL for assessment view page."""
  return urlparse.urljoin(utils.get_url_root(), utils.view_url_for(assessment))


def _build_status_comment(assessment, initial_assessment):
  """Returns status message if status gets changed or None otherwise."""
  if initial_assessment.status == assessment.status:
    return None, None

  verifiers = _get_roles(assessment).get('Verifiers')
  status_text = assessment.status
  if verifiers:
    status = _VERIFIER_STATUSES.get(
        (initial_assessment.status, assessment.status, assessment.verified))
    # Corner case for custom status text.
    if assessment.verified and assessment.status == 'Completed':
      status_text = '%s and Verified' % status_text
  else:
    status = _NO_VERIFIER_STATUSES.get(
        (initial_assessment.status, assessment.status))

  if status:
    return status, _STATUS_CHANGE_COMMENT_TMPL % (
        status_text, _get_assessment_url(assessment))

  return None, None


def _fill_current_value(issue_params, assessment, initial_info):
  """Fills unchanged props with current values."""
  current_issue_params = {}
  for name, api_name in _ISSUE_TRACKER_UPDATE_FIELDS:
    current_issue_params[api_name] = initial_info.get(name)
  issue_params = dict(current_issue_params, **issue_params)

  if 'status' not in issue_params:
    # Resend status on any change.
    status_value = issues.STATUSES.get(assessment.status)
    if status_value:
      issue_params['status'] = status_value

  if 'hotlist_ids' not in issue_params:
    # Resend hotlists on any change.
    current_hotlist_id = initial_info.get('hotlist_id')
    issue_params['hotlist_ids'] = [current_hotlist_id] if (
        current_hotlist_id) else []

  if 'ccs' not in issue_params:
    current_cc_list = initial_info.get('cc_list')
    if current_cc_list:
      issue_params['ccs'] = current_cc_list

  return issue_params


def _get_added_comment_id(src):
  """Returns comment ID from given request."""
  if not src:
    return None

  actions = src.get('actions') or {}
  related = actions.get('add_related') or []

  if not related:
    return None

  related_obj = related[0]

  if related_obj.get('type') != 'Comment':
    return None

  return related_obj.get('id')


def _get_added_comment_text(src):
  """Returns comment text from given request."""
  comment_id = _get_added_comment_id(src)
  if comment_id is not None:
    comment_row = db.session.query(
        all_models.Comment.description,
        all_models.Person.email,
        all_models.Person.name
    ).outerjoin(
        all_models.Person,
        all_models.Person.id == all_models.Comment.modified_by_id,
    ).filter(
        all_models.Comment.id == comment_id
    ).first()
    if comment_row is not None:
      desc, creator_email, creator_name = comment_row
      if not creator_name:
        creator_name = creator_email
      return html2text.HTML2Text().handle(desc).strip('\n'), creator_name
  return None, None


def _is_issue_tracker_enabled(audit=None):
  """Returns a boolean whether issue tracker integration feature is enabled.

  Args:
    audit: An optional instance of Audit model. If given function check if
        issue tracker integration is enabled for given audit as well.

  Returns:
    A boolean, True if feature is enabled or False otherwise.
  """
  if not _ISSUE_TRACKER_ENABLED:
    return False

  if audit is not None:
    audit_issue_tracker_info = audit.issue_tracker or {}

    if not bool(audit_issue_tracker_info.get('enabled')):
      return False

  return True


def _create_issuetracker_issue(assessment, issue_tracker_info):
  """Collects information and sends a request to create external issue."""
  _normalize_issue_tracker_info(issue_tracker_info)

  person, acl, acr = (all_models.Person, all_models.AccessControlList,
                      all_models.AccessControlRole)
  reporter_email = db.session.query(
      person.email,
  ).join(
      acl,
      person.id == acl.person_id,
  ).join(
      acr,
      sa.and_(
          acl.ac_role_id == acr.id,
          acr.name == "Audit Captains",
      ),
  ).filter(
      acl.object_id == assessment.audit_id,
      acl.object_type == all_models.Audit.__name__,
  ).order_by(
      person.email,
  ).first()

  if reporter_email:
    reporter_email = reporter_email.email

  comment = [_INITIAL_COMMENT_TMPL % _get_assessment_url(assessment)]
  test_plan = assessment.test_plan
  if test_plan:
    comment.extend([
        'Following is the assessment Requirements/Assessment Procedure '
        'from GGRC:',
        html2text.HTML2Text().handle(test_plan).strip('\n'),
    ])

  hotlist_id = issue_tracker_info.get('hotlist_id')

  issue_params = {
      'component_id': issue_tracker_info['component_id'],
      'hotlist_ids': [hotlist_id] if hotlist_id else [],
      'title': issue_tracker_info['title'],
      'type': issue_tracker_info['issue_type'],
      'priority': issue_tracker_info['issue_priority'],
      'severity': issue_tracker_info['issue_severity'],
      'reporter': reporter_email,
      'assignee': '',
      'verifier': '',
      'ccs': [],
      'comment': '\n'.join(comment),
  }

  assignee = issue_tracker_info.get('assignee')
  if assignee:
    issue_params['status'] = 'ASSIGNED'
    issue_params['assignee'] = assignee
    issue_params['verifier'] = assignee

  cc_list = issue_tracker_info.get('cc_list')
  if cc_list is not None:
    issue_params['ccs'] = cc_list

  res = issues.Client().create_issue(issue_params)
  return res['issueId']


def _create_issuetracker_info(assessment, issue_tracker_info):
  """Creates an entry for IssueTracker model."""
  if not issue_tracker_info.get('title'):
    issue_tracker_info['title'] = assessment.title

  if (issue_tracker_info.get('enabled') and
          _is_issue_tracker_enabled(audit=assessment.audit)):

    assignee_email, cc_list = _collect_issue_emails(assessment)
    if assignee_email is not None:
      issue_tracker_info['assignee'] = assignee_email
      issue_tracker_info['cc_list'] = cc_list

    try:
      issue_id = _create_issuetracker_issue(assessment, issue_tracker_info)
    except integrations_errors.Error as error:
      logger.error(
          'Unable to create a ticket while creating assessment ID=%d: %s',
          assessment.id, error)
      issue_tracker_info = {
          'enabled': False,
      }
      assessment.add_warning('issue_tracker', 'Unable to create a ticket.')
    else:
      issue_tracker_info['issue_id'] = issue_id
      issue_tracker_info['issue_url'] = _ISSUE_URL_TMPL % issue_id
  else:
    issue_tracker_info = {
        'enabled': False,
    }

  all_models.IssuetrackerIssue.create_or_update_from_dict(
      assessment, issue_tracker_info)


def _update_issuetracker_issue(assessment, issue_tracker_info,
                               initial_assessment, initial_info, request):
  """Collects information and sends a request to update external issue."""
  # pylint: disable=too-many-locals
  issue_id = issue_tracker_info.get('issue_id')
  if not issue_id:
    return

  comments = []

  # Handle switching of 'enabled' property.
  enabled = issue_tracker_info.get('enabled', False)
  if initial_info.get('enabled', False) != enabled:
    # Add comment about toggling feature and process further.
    comments.append(_ENABLED_TMPL if enabled else _DISABLED_TMPL)
  elif not enabled:
    # If feature remains in the same status which is 'disabled'.
    return

  _normalize_issue_tracker_info(issue_tracker_info)

  issue_params = _handle_basic_props(issue_tracker_info, initial_info)

  # Handle status update.
  status_value, status_comment = _build_status_comment(
      assessment, initial_assessment)
  if status_value:
    issue_params['status'] = status_value
    comments.append(status_comment)

  # Attach user comments if any.
  comment_text, comment_author = _get_added_comment_text(request)
  if comment_text is not None:
    comments.append(
        _COMMENT_TMPL % (
            comment_author, comment_text, _get_assessment_url(assessment)))

  if comments:
    issue_params['comment'] = '\n\n'.join(comments)

  # Handle hotlist ID update.
  hotlist_id = issue_tracker_info.get('hotlist_id')
  if hotlist_id is not None and hotlist_id != initial_info.get('hotlist_id'):
    issue_params['hotlist_ids'] = [hotlist_id] if hotlist_id else []

  # handle assignee and cc_list update
  assignee_email, cc_list = _collect_issue_emails(assessment)
  if assignee_email is not None:
    issue_tracker_info['assignee'] = assignee_email
    issue_params['assignee'] = assignee_email
    issue_params['verifier'] = assignee_email
    issue_params['ccs'] = cc_list

  if issue_params:
    # Resend all properties upon any change.
    issue_params = _fill_current_value(issue_params, assessment, initial_info)
    issues.Client().update_issue(issue_id, issue_params)


def _update_issuetracker_info(assessment, issue_tracker_info):
  """Updates an entry for IssueTracker model."""
  if not _is_issue_tracker_enabled(audit=assessment.audit):
    issue_tracker_info['enabled'] = False

  all_models.IssuetrackerIssue.create_or_update_from_dict(
      assessment, issue_tracker_info)
