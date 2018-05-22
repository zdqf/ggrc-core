# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Integration test for Clonable mixin"""
from collections import OrderedDict

import ddt
import mock

from ggrc import db
from ggrc import models
from ggrc.models import all_models
from ggrc.models.hooks import issue_tracker
from ggrc.integrations import utils
from ggrc.access_control.role import AccessControlRole

from integration.ggrc.models import factories
from integration.ggrc import generator
from integration.ggrc.access_control import acl_helper
from integration.ggrc.snapshotter import SnapshotterBaseTestCase


@ddt.ddt
class TestIssueTrackerIntegration(SnapshotterBaseTestCase):
  """Test set for IssueTracker integration functionality."""

  # pylint: disable=invalid-name

  def setUp(self):
    # pylint: disable=super-on-old-class
    # pylint seems to get confused, mro chain successfully resolves and returns
    # <type 'object'> as last entry.
    super(TestIssueTrackerIntegration, self).setUp()

    self.client.get('/login')

  def test_update_issuetracker_info(self):
    """Test that Issue Tracker issues are updated by the utility."""
    cli_patch = mock.patch.object(utils.issues, 'Client')
    hook_patch = mock.patch.object(issue_tracker, '_is_issue_tracker_enabled',
                                   return_value=True)
    with cli_patch, hook_patch:
      iti_issue_id = []
      for _ in xrange(2):
        iti = factories.IssueTrackerIssueFactory()
        iti_issue_id.append(iti.issue_id)
        asmt = iti.issue_tracked_obj
        asmt_id = asmt.id
        audit = asmt.audit
        self.api.modify_object(audit, {
            'issue_tracker': {
                'enabled': True,
                'component_id': '11111',
                'hotlist_id': '222222',
            },
        })
        asmt = db.session.query(models.Assessment).get(asmt_id)
        self.api.modify_object(asmt, {
            'issue_tracker': {
                'enabled': True,
                'component_id': '11111',
                'hotlist_id': '222222',
            },
        })
        asmt = db.session.query(models.Assessment).get(asmt_id)
        self.api.modify_object(asmt, {
            'issue_tracker': {
                'enabled': True,
                'component_id': '11111',
                'hotlist_id': '222222',
                'issue_priority': 'P4',
                'issue_severity': 'S3',
            },
        })
      self.api.delete(asmt)

    cli_mock = mock.MagicMock()
    cli_mock.update_issue.return_value = None
    cli_mock.search.return_value = {
        'issues': [
            {
                'issueId': iti_issue_id[0],
                'issueState': {
                    'status': 'FIXED', 'type': 'bug2',
                    'priority': 'P2', 'severity': 'S2',
                },
            },
        ],
        'next_page_token': None,
    }

    with mock.patch.object(utils.issues, 'Client', return_value=cli_mock):
      utils.sync_issue_tracker_statuses()
      cli_mock.update_issue.assert_called_once_with(
          iti_issue_id[0], {
              'status': 'ASSIGNED',
              'priority': u'P4',
              'type': None,
              'severity': u'S3',
          })

  # pylint: disable=unused-argument
  @mock.patch('ggrc.integrations.issues.Client.update_issue')
  def test_update_issuetracker_assignee(self, mocked_update_issue):
    """Test assignee sync in case it has been updated."""
    email1 = "email1@example.com"
    email2 = "email2@example.com"
    assignee_role_id = AccessControlRole.query.filter_by(
        object_type="Assessment",
        name="Assignees"
    ).first().id
    assignees = [factories.PersonFactory(email=email2),
                 factories.PersonFactory(email=email1)]
    iti_issue_id = []
    iti = factories.IssueTrackerIssueFactory(enabled=True)
    iti_issue_id.append(iti.issue_id)
    asmt = iti.issue_tracked_obj
    with mock.patch.object(issue_tracker, '_is_issue_tracker_enabled',
                           return_value=True):
      acl = [acl_helper.get_acl_json(assignee_role_id, assignee.id)
             for assignee in assignees]
      self.api.put(asmt, {
          "access_control_list": acl
      })
      kwargs = {'status': 'ASSIGNED',
                'component_id': None,
                'severity': None,
                'title': iti.title,
                'hotlist_ids': [],
                'priority': None,
                'assignee': email1,
                'verifier': email1,
                'ccs': [email2]}
      mocked_update_issue.assert_called_once_with(iti_issue_id[0], kwargs)

  # pylint: disable=protected-access
  @ddt.data(
      ('Not Started', {'status': 'ASSIGNED'}),
      ('In Progress', {'status': 'ASSIGNED'}),
      ('In Review', {'status': 'FIXED'}),
      ('Rework Needed', {'status': 'ASSIGNED'}),
      ('Completed', {'status': 'VERIFIED',
                     'comment': issue_tracker._STATUS_CHANGE_COMMENT_TMPL}),
      ('Deprecated', {'status': 'OBSOLETE',
                      'comment': issue_tracker._STATUS_CHANGE_COMMENT_TMPL}),
  )
  @ddt.unpack
  @mock.patch('ggrc.integrations.issues.Client.update_issue')
  def test_change_assessment_status(self, status,
                                    additional_kwargs,
                                    mocked_update_issue):
    """Issue status should be changed for assessment
    with {status} status."""
    email1 = "email1@example.com"
    assignee_role_id = AccessControlRole.query.filter_by(
        object_type="Assessment",
        name="Assignees"
    ).first().id
    assignees = [factories.PersonFactory(email=email1)]
    iti_issue_id = []
    iti = factories.IssueTrackerIssueFactory(enabled=True)
    iti_issue_id.append(iti.issue_id)
    asmt = iti.issue_tracked_obj
    with mock.patch.object(issue_tracker, '_is_issue_tracker_enabled',
                           return_value=True):
      acl = [acl_helper.get_acl_json(assignee_role_id, assignee.id)
             for assignee in assignees]
      self.api.put(asmt, {
          "access_control_list": acl,
          "status": status,
      })
      kwargs = {'component_id': None,
                'severity': None,
                'title': iti.title,
                'hotlist_ids': [],
                'priority': None,
                'assignee': email1,
                'verifier': email1,
                'ccs': []}
      asmt_link = issue_tracker._get_assessment_url(asmt)
      if 'comment' in additional_kwargs:
        additional_kwargs['comment'] = \
            additional_kwargs['comment'] % (status, asmt_link)
      kwargs.update(additional_kwargs)
      mocked_update_issue.assert_called_once_with(iti_issue_id[0], kwargs)

      issue = db.session.query(models.IssuetrackerIssue).get(iti.id)
      self.assertEqual(issue.assignee, email1)
      self.assertEqual(issue.cc_list, "")

  @mock.patch('ggrc.integrations.issues.Client.create_issue')
  @mock.patch('ggrc.integrations.issues.Client.update_issue')
  def test_basic_import(self, mock_create_issue, mock_update_issue):
    """Test basic import functionality."""
    with mock.patch.object(issue_tracker, '_is_issue_tracker_enabled',
                           return_value=True):
      # update existing object
      iti = factories.IssueTrackerIssueFactory(enabled=True)
      asmt = iti.issue_tracked_obj
      audit = asmt.audit
      response = self.import_data(OrderedDict([
          ('object_type', 'Assessment'),
          ('Code*', asmt.slug),
          ('Audit', audit.slug),
      ]), dry_run=False)
      self._check_csv_response(response, {})

      # import new object
      response = self.import_data(OrderedDict([
          ('object_type', 'Assessment'),
          ('Code*', 'Test Code'),
          ('Audit', audit.slug),
          ('Creators', 'user@example.com'),
          ('Assignees*', 'user@example.com'),
          ('Title', 'Some Title'),
      ]), dry_run=False)
      self._check_csv_response(response, {})


@mock.patch('ggrc.models.hooks.issue_tracker._is_issue_tracker_enabled',
            return_value=True)
@mock.patch('ggrc.integrations.issues.Client')
class TestIssueTrackerIntegrationPeople(SnapshotterBaseTestCase):
  """Test people used in IssueTracker Issues."""

  EMAILS = {
      'Audit Captains': {'audit_captain_1@example.com',
                         'audit_captain_2@example.com'},
      'Auditors': {'auditor_1@example.com', 'auditor_2@example.com'},
      'Creators': {'creator_1@example.com', 'creator_2@example.com'},
      'Assignees': {'assignee_1@example.com', 'assignee_2@example.com'},
      'Verifiers': {'verifier_1@example.com', 'verifier_2@example.com'},
      'Primary Contacts': {'primary_contact_1@example.com',
                           'primary_contact_2@example.com'},
      'Secondary Contacts': {'secondary_contact_1@example.com',
                             'secondary_contact_2@example.com'},
      'Custom Role': {'curom_role_1@example.com'},
  }

  ROLE_NAMES = (
      'Creators',
      'Assignees',
      'Verifiers',
      'Primary Contacts',
      'Secondary Contacts',
      'Custom Role'
  )

  def setUp(self):
    super(TestIssueTrackerIntegrationPeople, self).setUp()
    self.generator = generator.ObjectGenerator()

    factories.AccessControlRoleFactory(
        name='Custom Role',
        internal=False,
        object_type='Assessment',
    )

    # fetch all roles mentioned in self.EMAILS
    self.roles = {
        role.name: role
        for role in all_models.AccessControlRole.query.filter(
            all_models.AccessControlRole.name.in_(
                self.EMAILS.keys(),
            ),
        )
    }

    with factories.single_commit():
      self.audit = factories.AuditFactory()

      self.people = {
          role_name: [factories.PersonFactory(email=email)
                      for email in emails]
          for role_name, emails in self.EMAILS.iteritems()
      }

  def setup_audit_people(self, role_name_to_people):
    """Assign roles to people provided."""
    with factories.single_commit():
      for role_name, people in role_name_to_people.iteritems():
        role = self.roles[role_name]
        for person in people:
          factories.AccessControlListFactory(person=person,
                                             ac_role=role,
                                             object=self.audit)

  def create_asmt_with_issue_tracker(self, role_name_to_people,
                                     issue_tracker=None):
    """Create Assessment with issue_tracker parameters and ACL."""
    access_control_list = acl_helper.get_acl_list({
        person.id: self.roles[role_name].id
        for role_name, people in role_name_to_people.iteritems()
        for person in people
    })
    issue_tracker_with_defaults = {
        'enabled': True,
        'component_id': hash('Default Component id'),
        'hotlist_id': hash('Default Hotlist id'),
        'issue_type': 'Default Issue type',
        'issue_priority': 'Default Issue priority',
        'issue_severity': 'Default Issue severity',
    }
    issue_tracker_with_defaults.update(issue_tracker or {})

    _, asmt = self.generator.generate_object(
        all_models.Assessment,
        data={
            'audit': {'id': self.audit.id, 'type': self.audit.type},
            'issue_tracker': issue_tracker_with_defaults,
            'access_control_list': access_control_list,
        }
    )

    return asmt

  def test_new_assessment_people(self, client_mock, _):
    """External Issue for Assessment contains correct people."""
    client_instance = client_mock.return_value
    client_instance.create_issue.return_value = {'issueId': 42}

    self.setup_audit_people({
        role_name: people for role_name, people in self.people.items()
        if role_name in ('Audit Captains', 'Auditors')
    })

    component_id = hash('Component id')
    hotlist_id = hash('Hotlist id')
    issue_type = 'Issue type'
    issue_priority = 'Issue priority'
    issue_severity = 'Issue severity'

    asmt = self.create_asmt_with_issue_tracker(
        role_name_to_people={
            role_name: people for role_name, people in self.people.items()
            if role_name in self.ROLE_NAMES
        },
        issue_tracker={
            'component_id': component_id,
            'hotlist_id': hotlist_id,
            'issue_type': issue_type,
            'issue_priority': issue_priority,
            'issue_severity': issue_severity,
        },
    )

    expected_cc_list = list(
        self.EMAILS['Assignees'] - {min(self.EMAILS['Assignees'])}
    )

    # pylint: disable=protected-access; we assert by non-exported constants
    client_instance.create_issue.assert_called_once_with({
        # common fields
        'comment': (issue_tracker._INITIAL_COMMENT_TMPL %
                    issue_tracker._get_assessment_url(asmt)),
        'component_id': component_id,
        'hotlist_ids': [hotlist_id],
        'priority': issue_priority,
        'severity': issue_severity,
        'status': 'ASSIGNED',
        'title': asmt.title,
        'type': issue_type,

        # person-related fields
        'reporter': min(self.EMAILS['Audit Captains']),
        'assignee': min(self.EMAILS['Assignees']),
        'verifier': min(self.EMAILS['Assignees']),
        'ccs': expected_cc_list,
    })

  def test_missing_audit_captains(self, client_mock, _):
    """Reporter email is None is no Audit Captains present."""
    client_instance = client_mock.return_value
    client_instance.create_issue.return_value = {'issueId': 42}

    self.setup_audit_people({
        'Audit Captains': [],
        'Auditors': self.people['Auditors'],
    })

    self.create_asmt_with_issue_tracker(
        role_name_to_people={
            role_name: people for role_name, people in self.people.items()
            if role_name in ('Creators', 'Assignees', 'Verifiers')
        },
    )

    client_instance.create_issue.assert_called_once()
    self.assertIs(client_instance.create_issue.call_args[0][0]['reporter'],
                  None)
