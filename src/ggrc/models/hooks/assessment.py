# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
  Assessment generator hooks

  We are applying assessment template properties and make
  new relationships and custom attributes
"""
import collections
import itertools
import logging

from sqlalchemy import orm

from ggrc import db
from ggrc import access_control
from ggrc.login import get_current_user_id
from ggrc.models import all_models
from ggrc.models.hooks import common
from ggrc.models.hooks.issue_tracker import assessment_integration
from ggrc.models.exceptions import StatusValidationError
from ggrc.services import signals
from ggrc.utils import referenced_objects


logger = logging.getLogger(__name__)


def _validate_assessment_done_state(old_value, obj):
  """Checks if it's allowed to set done state from not done."""
  new_value = obj.status
  if old_value in obj.NOT_DONE_STATES and \
     new_value in obj.DONE_STATES:
    if hasattr(obj, "preconditions_failed") and obj.preconditions_failed:
      raise StatusValidationError("CA-introduced completion "
                                  "preconditions are not satisfied. "
                                  "Check preconditions_failed "
                                  "of items of self.custom_attribute_values")


def _handle_assessment(assessment, src):
  """Handles auto calculated properties for Assessment model."""
  snapshot_dict = src.get('object') or {}
  common.map_objects(assessment, snapshot_dict)
  common.map_objects(assessment, src.get('audit'))
  snapshot = referenced_objects.get("Snapshot", snapshot_dict.get('id'))

  if not src.get('_generated') and not snapshot:
    return

  template = referenced_objects.get(
      src.get('template', {}).get('type'),
      src.get('template', {}).get('id'),
  )
  audit = referenced_objects.get(
      src['audit']['type'],
      src['audit']['id'],
  )
  relate_assignees(assessment, snapshot, template, audit)
  relate_ca(assessment, template)
  assessment.title = u'{} assessment for {}'.format(
      snapshot.revision.content['title'],
      audit.title,
  )

  if not template:
    # Assessment test plan should inherit test plan of snapshot
    assessment.test_plan = snapshot.revision.content.get("test_plan")
    return

  assessment.test_plan_procedure = template.test_plan_procedure
  assessment.test_plan = template.procedure_description
  if template.test_plan_procedure:
    copy_snapshot_plan(assessment, snapshot)
  if template.template_object_type:
    assessment.assessment_type = template.template_object_type


def init_hook():
  """Initializes hooks."""

  # pylint: disable=unused-variable
  @signals.Restful.collection_posted.connect_via(all_models.Assessment)
  def handle_assessment_post(sender, objects=None, sources=None, service=None):
    """Applies custom attribute definitions and maps people roles.

    Applicable when generating Assessment with template.

    Args:
      sender: A class of Resource handling the POST request.
      objects: A list of model instances created from the POSTed JSON.
      sources: A list of original POSTed JSON dictionaries.
    """
    del sender, service  # Unused

    db.session.flush()

    for assessment, src in itertools.izip(objects, sources):
      _handle_assessment(assessment, src)

    # Flush roles objects for generated assessments.
    db.session.flush()

    for assessment, src in itertools.izip(objects, sources):
      # Handling IssueTracker info here rather than in hooks/issue_tracker
      # would avoid querying same data (such as snapshots, audits and
      # templates) twice.
      assessment_integration.handle_assessment_create(assessment, src)

  # pylint: disable=unused-variable
  @signals.Restful.model_put.connect_via(all_models.Assessment)
  def handle_assessment_put(sender, obj=None, src=None, service=None):
    """Handles assessment update event."""
    del sender, src, service  # Unused
    common.ensure_field_not_changed(obj, 'audit')

  @signals.Restful.model_put_before_commit.connect_via(all_models.Assessment)
  def handle_assessment_done_state(sender, **kwargs):
    """Checks if it's allowed to set done state from not done."""
    del sender  # Unused arg
    obj = kwargs['obj']
    initial_state = kwargs['initial_state']
    old_value = initial_state.status
    try:
      _validate_assessment_done_state(old_value, obj)
    except StatusValidationError as error:
      db.session.rollback()
      raise error


def generate_assignee_relations(assessment,
                                assignee_ids,
                                verifier_ids,
                                creator_ids):
  """Generates db relations to assessment for sent role ids.

    Args:
        assessment (model instance): Assessment model
        assignee_ids (list): list of person ids
        verifier_ids (list): list of person ids
        creator_ids (list): list of person ids
  """
  people = set(assignee_ids + verifier_ids + creator_ids)
  person_dict = {i.id: i for i in all_models.Person.query.filter(
      all_models.Person.id.in_(people)
  )}

  person_roles = []
  for person_id in people:
    person = person_dict.get(person_id)
    if person is None:
      continue
    if person_id in assignee_ids:
      person_roles.append((person, "Assignees"))
    if person_id in verifier_ids:
      person_roles.append((person, "Verifiers"))
    if person_id in creator_ids:
      person_roles.append((person, "Creators"))

  ac_roles = access_control.role.get_ac_roles_for(assessment.type)

  db.session.add_all(
      all_models.AccessControlList(
          ac_role=ac_roles[role],
          person=person,
          object=assessment
      ) for person, role in person_roles
  )


def get_people_ids_based_on_role(assignee_role,
                                 default_role,
                                 template_settings,
                                 acl_dict):
  """Get people_ids base on role and template settings."""
  if not template_settings.get(assignee_role):
    return []
  template_role = template_settings[assignee_role]
  if isinstance(template_role, list):
    return template_role
  return acl_dict.get(template_role, acl_dict.get(default_role)) or []


def generate_role_object_dict(snapshot, audit):
  """Generate roles dict for sent snapshot and audit.

  returns dict of roles with key as role name and list of people ids as values.
  """

  acr_dict = access_control.role.get_custom_roles_for(snapshot.child_type)
  audit_acr = access_control.role.get_custom_roles_for("Audit")
  auditors_role = next(id_ for id_, val in audit_acr.iteritems()
                       if val == "Auditors")
  leads_role = next(id_ for id_, val in audit_acr.iteritems()
                    if val == "Audit Captains")

  acl_dict = collections.defaultdict(list)
  # populated content should have access_control_list
  for acl in snapshot.revision.content["access_control_list"]:
    acr = acr_dict.get(acl["ac_role_id"])
    if not acr:
      # This can happen when we try to create an assessment for a control that
      # had a custom attribute role removed. This can not cause a bug as we
      # only use the acl_list for getting new assessment assignees and those
      # can only be from non editable roles, meaning the roles that we actually
      # need can not be removed. Non essential roles that are removed might
      # should not affect this assessment generation.
      logger.info("Snapshot %d contains deleted role %d",
                  snapshot.id, acl["ac_role_id"])
      continue
    acl_dict[acr].append(acl["person_id"])

  # populate Access Control List by generated role from the related Audit
  acl_dict["Audit Lead"].extend([acl.person_id
                                 for acl in audit.access_control_list
                                 if acl.ac_role_id == leads_role])
  auditors = [
      acl.person_id for acl in audit.access_control_list
      if acl.ac_role_id == auditors_role
  ]
  acl_dict["Auditors"].extend(auditors or acl_dict["Audit Lead"])
  return acl_dict


def relate_assignees(assessment, snapshot, template, audit):
  """Generates assignee list and relates them to Assessment objects

    Args:
        assessment (model instance): Assessment model
        snapshot (model instance): Snapshot,
        template (model instance): AssessmentTemplate model nullable,
        audit (model instance): Audit
  """
  if template:
    template_settings = template.default_people
  else:
    template_settings = {"assignees": "Principal Assignees",
                         "verifiers": "Auditors"}
  acl_dict = generate_role_object_dict(snapshot, audit)
  assignee_ids = get_people_ids_based_on_role("assignees",
                                              "Audit Lead",  # default assignee
                                              template_settings,
                                              acl_dict)
  verifier_ids = get_people_ids_based_on_role("verifiers",
                                              "Auditors",  # default verifier
                                              template_settings,
                                              acl_dict)
  generate_assignee_relations(assessment,
                              assignee_ids,
                              verifier_ids,
                              [get_current_user_id()])


def relate_ca(assessment, template):
  """Generates custom attribute list and relates it to Assessment objects

    Args:
        assessment (model instance): Assessment model
        template: Assessment Temaplte instance (may be None)
  """
  if not template:
    return None

  ca_definitions = all_models.CustomAttributeDefinition.query.options(
      orm.undefer_group('CustomAttributeDefinition_complete'),
  ).filter_by(
      definition_id=template.id,
      definition_type="assessment_template",
  ).order_by(
      all_models.CustomAttributeDefinition.id
  )
  created_cads = []
  for definition in ca_definitions:
    cad = all_models.CustomAttributeDefinition(
        title=definition.title,
        definition=assessment,
        attribute_type=definition.attribute_type,
        multi_choice_options=definition.multi_choice_options,
        multi_choice_mandatory=definition.multi_choice_mandatory,
        mandatory=definition.mandatory,
        helptext=definition.helptext,
        placeholder=definition.placeholder,
    )
    db.session.add(cad)
    created_cads.append(cad)
  return created_cads


def copy_snapshot_plan(assessment, snapshot):
  """Copy test plan of Snapshot into Assessment"""
  snapshot_plan = snapshot.revision.content.get("test_plan", "")
  if assessment.test_plan and snapshot_plan:
    assessment.test_plan += "<br>"
    assessment.test_plan += snapshot_plan
  elif snapshot_plan:
    assessment.test_plan = snapshot_plan
