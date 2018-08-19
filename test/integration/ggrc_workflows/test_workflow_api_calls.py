# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests Workflow related API calls."""

import datetime
import unittest

import ddt
import freezegun

from ggrc.models import all_models

from integration.ggrc import TestCase
from integration.ggrc.api_helper import Api
from integration.ggrc.access_control import acl_helper
from integration.ggrc.models import factories
from integration.ggrc_workflows import generator as wf_generator
from integration.ggrc_workflows.models import factories as wf_factories


WF_ROLES = {
    role.name: role.id
    for role in all_models.AccessControlRole.eager_query().filter(
        all_models.AccessControlRole.object_type == "Workflow").all()
}


@ddt.ddt  # pylint: disable=too-many-public-methods
class TestWorkflowsApiPost(TestCase):
  """Test class for ggrc workflow api post action."""

  def setUp(self):
    super(TestWorkflowsApiPost, self).setUp()
    self.api = Api()
    self.generator = wf_generator.WorkflowsGenerator()
    self.wf_admin_id = all_models.Person.query.first().id
    with factories.single_commit():
      self.people_ids = [factories.PersonFactory().id for _ in xrange(6)]

  def tearDown(self):
    pass

  def _delete_and_check_related_acl(self, related_model, exp_acl_count,
                                    is_deleted):
    """Delete related model and check remaining ACL count.

    Args:
        related_model: related model class
        exp_acl_count: expected related ACL count after delete operation
        is_deleted: is related object already deleted
    """
    if is_deleted:
      related_count = related_model.query.count()
      self.assertEqual(related_count, 0)
    else:
      related = related_model.query.one()
      response = self.api.delete(related)
      self.assert200(response)

    related_acl_count = all_models.AccessControlList.query.filter(
        all_models.AccessControlList.object_type == related_model.__name__
    ).count()
    self.assertEqual(related_acl_count, 0)

    bg_task_count = all_models.AccessControlList.query.filter(
        all_models.AccessControlList.object_type == "BackgroundTask"
    ).count()

    all_acl_count = all_models.AccessControlList.query.count()
    self.assertEqual(all_acl_count - bg_task_count, exp_acl_count)

  def test_acl_on_object_deletion(self):
    """Test related ACL records removed on related object delete"""
    self._create_propagation_acl_test_data()
    acl_count = all_models.AccessControlList.query.count()
    self.assertNotEqual(acl_count, 0)

    admin = all_models.Person.query.get(1)
    self.api.set_user(admin)

    related_models = (
        (all_models.CycleTaskEntry, 33, False),
        (all_models.TaskGroup, 21, False),
        (all_models.TaskGroupTask, 21, True),
        (all_models.Cycle, 3, False),
        (all_models.CycleTaskGroup, 3, True),
        (all_models.CycleTaskGroupObjectTask, 3, True),
    )
    for related_model, acl_count, is_deleted in related_models:
      self._delete_and_check_related_acl(related_model, acl_count, is_deleted)

  def test_acl_on_workflow_delete(self):
    """Test related ACL records removed on Workflow delete"""
    self._create_propagation_acl_test_data()
    acl_count = all_models.AccessControlList.query.count()
    self.assertNotEqual(acl_count, 0)

    admin = all_models.Person.query.get(1)
    self.api.set_user(admin)
    workflow = all_models.Workflow.query.one()
    response = self.api.delete(workflow)
    self.assert200(response)

    acl_count = all_models.AccessControlList.query.count()
    bg_acl_count = all_models.AccessControlList.query.filter(
        all_models.AccessControlList.object_type == "BackgroundTask"
    ).count()
    self.assertEqual(acl_count, bg_acl_count)

  def test_acl_for_new_related_object(self):
    """Test Workflow ACL propagation for new related objects."""
    data = self.get_workflow_dict()
    acl_map = {
        self.people_ids[0]: WF_ROLES['Admin'],
        self.people_ids[1]: WF_ROLES['Workflow Member'],
    }
    data["workflow"]["access_control_list"] = acl_helper.get_acl_list(acl_map)
    data["workflow"]["unit"] = "week"
    data["workflow"]["repeat_every"] = 1
    response = self.api.post(all_models.Workflow, data)
    self.assertEqual(response.status_code, 201)

    data = self.get_task_group_dict(response.json["workflow"])
    data["task_group"]["contact"]["id"] = self.people_ids[2]
    data["task_group"]["contact"]["href"] = "/api/people/{}".format(
        self.people_ids[2])
    response = self.api.post(all_models.TaskGroup, data)
    self.assertEqual(response.status_code, 201)

    task_group = all_models.TaskGroup.eager_query().one()
    data = self.get_task_dict(task_group)
    data["task_group_task"]["start_date"] = "2018-01-04"
    data["task_group_task"]["end_date"] = "2018-01-05"
    response = self.api.post(all_models.TaskGroupTask, data)
    self.assertEqual(response.status_code, 201)

    workflow = all_models.Workflow.query.one()
    with freezegun.freeze_time("2018-01-05"):  # Generate 1 cycle
      self.generator.activate_workflow(workflow)

    cycle_task = all_models.CycleTaskGroupObjectTask.query.one()
    cycle = all_models.Cycle.query.one()
    data = self.get_comment_dict(cycle_task, cycle)
    response = self.api.post(all_models.CycleTaskEntry, data)
    self.assertEqual(response.status_code, 201)

    self._check_propagated_acl(3)

  @ddt.data('Admin', 'Workflow Member')
  def test_tg_assignee(self, role_name):
    """Test TaskGroup assignee already has {0} role."""
    data = self.get_workflow_dict()
    init_acl = {
        self.people_ids[0]: WF_ROLES['Admin'],
        self.people_ids[1]: WF_ROLES[role_name],
    }
    data['workflow']['access_control_list'] = acl_helper.get_acl_list(init_acl)
    response = self.api.post(all_models.Workflow, data)
    self.assertEqual(response.status_code, 201)

    data = self.get_task_group_dict(response.json["workflow"])
    data["task_group"]["contact"]["id"] = self.people_ids[1]
    data["task_group"]["contact"]["href"] = "/api/people/{}".format(
        self.people_ids[1])
    response = self.api.post(all_models.TaskGroup, data)
    self.assertEqual(response.status_code, 201)

    workflow = all_models.Workflow.query.one()
    task_group = all_models.TaskGroup.query.one()

    actual_acl = all_models.AccessControlList.eager_query().filter(
        all_models.AccessControlList.person_id == task_group.contact_id,
    ).all()
    self.assertEqual(len(actual_acl), 3)

    actual = {
        (acl.object_type, acl.object_id)
        for acl in actual_acl
    }
    self.assertIn((workflow.type, workflow.id), actual)
    self.assertIn((task_group.type, task_group.id), actual)

  def test_task_group_assignee_gets_workflow_member(self):  # noqa pylint: disable=invalid-name
    """Test TaskGroup assignee gets WorkflowMember role."""
    data = self.get_workflow_dict()
    init_acl = {
        self.people_ids[0]: WF_ROLES['Admin'],
        self.people_ids[1]: WF_ROLES['Workflow Member'],
    }
    data['workflow']['access_control_list'] = acl_helper.get_acl_list(init_acl)
    response = self.api.post(all_models.Workflow, data)
    self.assertEqual(response.status_code, 201)

    data = self.get_task_group_dict(response.json["workflow"])
    data["task_group"]["contact"]["id"] = self.people_ids[2]
    data["task_group"]["contact"]["href"] = "/api/people/{}".format(
        self.people_ids[2])
    response = self.api.post(all_models.TaskGroup, data)
    self.assertEqual(response.status_code, 201)

    workflow = all_models.Workflow.query.one()
    task_group = all_models.TaskGroup.query.one()

    parent_acl = all_models.AccessControlList.eager_query().filter(
        all_models.AccessControlList.person_id == task_group.contact_id,
        all_models.AccessControlList.object_type == workflow.type,
        all_models.AccessControlList.object_id == workflow.id
    ).one()
    tg_acl = all_models.AccessControlList.eager_query().filter(
        all_models.AccessControlList.person_id == task_group.contact_id,
        all_models.AccessControlList.object_type == task_group.type,
        all_models.AccessControlList.object_id == task_group.id
    ).one()
    self.assertEqual(parent_acl.ac_role.name, "Workflow Member")
    # Below we are using parent.parent to jump over the intermediary
    # relationship.
    self.assertEqual(tg_acl.parent.parent.id, parent_acl.id)
    self.assertIn("Workflow Member", tg_acl.ac_role.name)

  def _create_propagation_acl_test_data(self):  # noqa pylint: disable=invalid-name
    """Create objects for Workflow ACL propagation test."""
    with freezegun.freeze_time("2017-08-9"):
      with factories.single_commit():
        workflow = wf_factories.WorkflowFactory(
            title='wf1',
            unit=all_models.Workflow.WEEK_UNIT,
            is_verification_needed=True,
            repeat_every=1)
        wf_factories.TaskGroupTaskFactory(
            title='tgt1',
            task_group=wf_factories.TaskGroupFactory(
                title='tg1',
                context=factories.ContextFactory(),
                workflow=workflow
            ),
            # One cycle should be created
            start_date=datetime.date(2017, 8, 3),
            end_date=datetime.date(2017, 8, 7)
        )
      self.generator.activate_workflow(workflow)
      cycle = all_models.Cycle.query.one()
      cycle_task = all_models.CycleTaskGroupObjectTask.query.one()
      wf_factories.CycleTaskEntryFactory(
          cycle=cycle,
          cycle_task_group_object_task=cycle_task,
          description="Cycle task comment",
      )
      workflow = all_models.Workflow.query.one()
      acl_map = {
          self.people_ids[0]: WF_ROLES['Admin'],
          self.people_ids[1]: WF_ROLES['Workflow Member'],
          self.people_ids[2]: WF_ROLES['Workflow Member'],
      }
      put_params = {'access_control_list': acl_helper.get_acl_list(acl_map)}
      response = self.api.put(workflow, put_params)
      self.assert200(response)

  def _check_propagated_acl(self, roles_count):
    """Check Workflow propagated ACL records.

    Args:
        roles_count: roles' count created in test
    """
    related_objects = (
        (all_models.TaskGroup.query.one().id, all_models.TaskGroup.__name__),
        (all_models.TaskGroupTask.query.one().id,
         all_models.TaskGroupTask.__name__),
        (all_models.Cycle.query.one().id, all_models.Cycle.__name__),
        (all_models.CycleTaskGroup.query.one().id,
         all_models.CycleTaskGroup.__name__),
        (all_models.CycleTaskGroupObjectTask.query.one().id,
         all_models.CycleTaskGroupObjectTask.__name__),
        (all_models.CycleTaskEntry.query.one().id,
         all_models.CycleTaskEntry.__name__)
    )
    related_count = len(related_objects) * 2  # *2 is for relationships
    bd_tasks_count = all_models.BackgroundTask.query.count()

    all_acl = [acl for acl in all_models.AccessControlList.eager_query().all()]
    self.assertEqual(
        len(all_acl),
        bd_tasks_count + roles_count + roles_count * related_count
    )

  def test_assign_workflow_acl(self):
    """Test propagation Workflow ACL roles on Workflow's update ACL records."""
    self._create_propagation_acl_test_data()
    self._check_propagated_acl(3)

  def test_unassign_workflow_acl(self):
    """Test propagation Workflow ACL roles on person unassigned."""
    self._create_propagation_acl_test_data()
    with freezegun.freeze_time("2017-08-9"):
      workflow = all_models.Workflow.query.one()
      acl_map = {
          self.people_ids[0]: WF_ROLES['Admin'],
          self.people_ids[1]: WF_ROLES['Workflow Member'],
      }
      put_params = {'access_control_list': acl_helper.get_acl_list(acl_map)}
      response = self.api.put(workflow, put_params)
      self.assert200(response)

    self._check_propagated_acl(2)

  def test_post_workflow_with_acl(self):
    """Test PUT workflow with ACL."""
    data = self.get_workflow_dict()

    exp_res = {
        self.wf_admin_id: WF_ROLES['Admin'],
        self.people_ids[0]: WF_ROLES['Admin'],
        self.people_ids[1]: WF_ROLES['Workflow Member'],
        self.people_ids[2]: WF_ROLES['Workflow Member'],
        self.people_ids[3]: WF_ROLES['Workflow Member']
    }
    data['workflow']['access_control_list'] = acl_helper.get_acl_list(exp_res)
    response = self.api.post(all_models.Workflow, data)
    self.assertEqual(response.status_code, 201)
    workflow = all_models.Workflow.eager_query().one()
    act_res = {acl.person_id: acl.ac_role_id
               for acl in workflow.access_control_list}
    self.assertDictEqual(exp_res, act_res)

  def test_update_workflow_acl_people(self):
    """Test PUT workflow with updated ACL."""
    data = self.get_workflow_dict()
    init_map = {
        self.wf_admin_id: WF_ROLES['Admin'],
        self.people_ids[0]: WF_ROLES['Workflow Member'],
    }
    data['workflow']['access_control_list'] = acl_helper.get_acl_list(init_map)
    response = self.api.post(all_models.Workflow, data)
    self.assertEqual(response.status_code, 201)
    exp_res = {
        self.people_ids[0]: WF_ROLES['Admin'],
        self.people_ids[1]: WF_ROLES['Admin'],
        self.people_ids[2]: WF_ROLES['Workflow Member'],
        self.people_ids[3]: WF_ROLES['Workflow Member'],
        self.people_ids[4]: WF_ROLES['Workflow Member']
    }
    workflow = all_models.Workflow.eager_query().one()
    put_params = {'access_control_list': acl_helper.get_acl_list(exp_res)}
    response = self.api.put(workflow, put_params)
    self.assert200(response)
    workflow = all_models.Workflow.eager_query().one()
    act_res = {acl.person_id: acl.ac_role_id
               for acl in workflow.access_control_list}
    self.assertDictEqual(exp_res, act_res)

  def test_send_invalid_data(self):
    """Test send invalid data on Workflow post."""
    data = self.get_workflow_dict()
    del data["workflow"]["title"]
    del data["workflow"]["context"]
    response = self.api.post(all_models.Workflow, data)
    self.assert400(response)
    # TODO: check why response.json["message"] is empty

  def test_create_one_time_workflows(self):
    """Test simple create one time Workflow over api."""
    data = self.get_workflow_dict()
    response = self.api.post(all_models.Workflow, data)
    self.assertEqual(response.status_code, 201)

  def test_create_weekly_workflow(self):
    """Test create valid weekly wf"""
    data = self.get_workflow_dict()
    data["workflow"]["repeat_every"] = 7
    data["workflow"]["unit"] = "day"
    data["workflow"]["title"] = "Weekly"
    response = self.api.post(all_models.Workflow, data)
    self.assertEqual(response.status_code, 201)

  def test_create_annually_workflow(self):
    """Test create valid annual wf"""
    data = self.get_workflow_dict()
    data["workflow"]["repeat_every"] = 12
    data["workflow"]["unit"] = "month"
    data["workflow"]["title"] = "Annually"
    response = self.api.post(all_models.Workflow, data)
    self.assertEqual(response.status_code, 201)

  @ddt.data("wrong value", 0, -4)
  def test_create_wrong_repeat_every_workflow(self, value):  # noqa pylint: disable=invalid-name
    """Test case for invalid repeat_every value"""
    data = self.get_workflow_dict()
    data["workflow"]["repeat_every"] = value
    data["workflow"]["unit"] = "month"
    data["workflow"]["title"] = "Wrong wf"
    response = self.api.post(all_models.Workflow, data)
    self.assertEqual(response.status_code, 400)

  def test_create_wrong_unit_workflow(self):
    """Test case for invalid unit value"""
    data = self.get_workflow_dict()
    data["workflow"]["repeat_every"] = 12
    data["workflow"]["unit"] = "wrong value"
    data["workflow"]["title"] = "Wrong wf"
    response = self.api.post(all_models.Workflow, data)
    self.assertEqual(response.status_code, 400)

  def test_create_task_group(self):
    """Test create task group over api."""
    wf_data = self.get_workflow_dict()
    wf_data["workflow"]["title"] = "Create_task_group"
    wf_response = self.api.post(all_models.Workflow, wf_data)

    data = self.get_task_group_dict(wf_response.json["workflow"])

    response = self.api.post(all_models.TaskGroup, data)
    self.assertEqual(response.status_code, 201)

  @staticmethod
  def get_workflow_dict():
    return {
        "workflow": {
            "custom_attribute_definitions": [],
            "custom_attributes": {},
            "title": "One_time",
            "description": "",
            "unit": None,
            "repeat_every": None,
            "notify_on_change": False,
            "task_group_title": "Task Group 1",
            "notify_custom_message": "",
            "is_verification_needed": True,
            "context": None,
        }
    }

  def get_task_group_dict(self, workflow):
    return {
        "task_group": {
            "custom_attribute_definitions": [],
            "custom_attributes": {},
            "_transient": {},
            "contact": {
                "id": self.wf_admin_id,
                "href": "/api/people/{}".format(self.wf_admin_id),
                "type": "Person"
            },
            "workflow": {
                "id": workflow["id"],
                "href": "/api/workflows/%d" % workflow["id"],
                "type": "Workflow"
            },
            "context": {
                "id": workflow["context"]["id"],
                "href": "/api/contexts/%d" % workflow["context"]["id"],
                "type": "Context"
            },
            "modal_title": "Create Task Group",
            "title": "Create_task_group",
            "description": "",
        }
    }

  def get_task_dict(self, task_group):
    return {
        "task_group_task": {
            "start_date": "2017-12-25",
            "end_date": "2017-12-31",
            "custom_attributes": {},
            "contact": {
                "id": self.wf_admin_id,
                "href": "/api/people/{}".format(self.wf_admin_id),
                "type": "Person"
            },
            "task_group": {
                "id": task_group.id,
                "href": "/api/task_groups/{}".format(task_group.id),
                "type": "TaskGroup"
            },
            "context": {
                "id": task_group.context_id,
                "href": "/api/contexts/{}".format(task_group.context_id),
                "type": "Context"
            },
            "title": "Create_task",
            "task_type": "text",
            "description": ""
        }
    }

  @staticmethod
  def get_comment_dict(cycle_task, cycle):
    return {
        "cycle_task_entry": {
            "custom_attributes": {},
            "cycle_task_group_object_task": {
                "id": cycle_task.id,
                "href": "/api/cycle_task_group_object_tasks/{}".format(
                    cycle_task.id),
                "type": "CycleTaskGroupObjectTask"
            },
            "cycle": {
                "id": cycle.id,
                "href": "/api/cycles/{}".format(cycle.id),
                "type": "Cycle"
            },
            "context": {
                "id": cycle.context_id,
                "href": "/api/contexts/{}".format(cycle.context_id),
                "type": "Context"
            },
            "is_declining_review": "",
            "description": "CT comment"
        }
    }

  @ddt.data({},
            {"repeat_every": 5, "unit": "month"})
  def test_repeat_multiplier_field(self, data):
    """Check repeat_multiplier is set to 0 after wf creation."""
    with factories.single_commit():
      workflow = wf_factories.WorkflowFactory(**data)
    workflow_id = workflow.id
    self.assertEqual(
        0, all_models.Workflow.query.get(workflow_id).repeat_multiplier)

  # TODO: Unskip in the patch 2
  @unittest.skip("Will be activated in patch 2")
  def test_change_to_one_time_wf(self):
    """Check repeat_every and unit can be set to Null only together."""
    with factories.single_commit():
      workflow = wf_factories.WorkflowFactory(repeat_every=12,
                                              unit="day")
    resp = self.api.put(workflow, {"repeat_every": None,
                                   "unit": None})
    self.assert200(resp)

  @ddt.data({"repeat_every": 5},
            {"unit": "month"})
  def test_change_repeat_every(self, data):
    """Check repeat_every or unit can not be changed once set."""
    with factories.single_commit():
      workflow = wf_factories.WorkflowFactory()
    resp = self.api.put(workflow, data)
    self.assert400(resp)

  def test_not_change_to_one_time_wf(self):
    """Check repeat_every or unit can't be set to Null separately.
    This test will be useful in the 2nd patch, where we allow to change
    WF setup
    """
    with factories.single_commit():
      workflow = wf_factories.WorkflowFactory(repeat_every=12,
                                              unit="day")
    resp = self.api.put(workflow, {"repeat_every": None})
    self.assert400(resp)
    resp = self.api.put(workflow, {"unit": None})
    self.assert400(resp)

  @ddt.data(True, False)
  def test_autogen_verification_flag(self, flag):
    """Check is_verification_needed flag for activate WF action."""
    with factories.single_commit():
      workflow = wf_factories.WorkflowFactory(is_verification_needed=flag)
      group = wf_factories.TaskGroupFactory(workflow=workflow)
      wf_factories.TaskGroupTaskFactory(task_group=group)
    data = [{
        "cycle": {
            "autogenerate": True,
            "isOverdue": False,
            "workflow": {
                "id": workflow.id,
                "type": "Workflow",
            },
            "context": {
                "id": workflow.context_id,
                "type": "Context",
            },
        }
    }]
    resp = self.api.send_request(
        self.api.client.post,
        api_link="/api/cycles",
        data=data)
    cycle_id = resp.json[0][1]["cycle"]["id"]
    self.assertEqual(
        flag, all_models.Cycle.query.get(cycle_id).is_verification_needed)

  @ddt.data(True, False)
  def test_verification_flag_positive(self, flag):  # noqa pylint: disable=invalid-name
    """is_verification_needed flag is changeable for DRAFT workflow."""
    with factories.single_commit():
      workflow = wf_factories.WorkflowFactory(is_verification_needed=flag)
    self.assertEqual(workflow.status, all_models.Workflow.DRAFT)
    workflow_id = workflow.id
    resp = self.api.put(workflow, {"is_verification_needed": not flag})
    self.assert200(resp)
    self.assertEqual(
        all_models.Workflow.query.get(workflow_id).is_verification_needed,
        not flag)

  @ddt.data(True, False)
  def test_verification_flag_negative(self, flag):
    """Test immutable verification flag on active workflows."""
    with freezegun.freeze_time("2017-08-10"):
      with factories.single_commit():
        workflow = wf_factories.WorkflowFactory(
            unit=all_models.Workflow.WEEK_UNIT,
            is_verification_needed=flag,
            repeat_every=1)
        wf_factories.TaskGroupTaskFactory(
            task_group=wf_factories.TaskGroupFactory(
                context=factories.ContextFactory(),
                workflow=workflow
            ),
            # Two cycles should be created
            start_date=datetime.date(2017, 8, 3),
            end_date=datetime.date(2017, 8, 7))
      workflow_id = workflow.id
      self.assertEqual(workflow.status, all_models.Workflow.DRAFT)
      self.generator.activate_workflow(workflow)
      workflow = all_models.Workflow.query.get(workflow_id)
      self.assertEqual(workflow.status, all_models.Workflow.ACTIVE)
      resp = self.api.put(workflow, {"is_verification_needed": not flag})
      self.assert400(resp)
      workflow = all_models.Workflow.query.get(workflow_id)
      self.assertEqual(workflow.is_verification_needed, flag)

      # End all current cycles
      for cycle in workflow.cycles:
        self.generator.modify_object(cycle, {'is_current': False})
      workflow = all_models.Workflow.query.filter(
          all_models.Workflow.id == workflow_id).first()
      self.assertEqual(workflow.status, all_models.Workflow.INACTIVE)
      resp = self.api.put(workflow, {"is_verification_needed": not flag})
      self.assert400(resp)
      workflow = all_models.Workflow.query.get(workflow_id)
      self.assertEqual(workflow.is_verification_needed, flag)

  @ddt.data(True, False)
  def test_not_change_vf_flag(self, flag):
    """Check is_verification_needed not change on update."""
    with factories.single_commit():
      workflow = wf_factories.WorkflowFactory(is_verification_needed=flag)
    workflow_id = workflow.id
    resp = self.api.put(workflow, {"is_verification_needed": flag})
    self.assert200(resp)
    self.assertEqual(
        flag,
        all_models.Workflow.query.get(workflow_id).is_verification_needed)

  @ddt.data(True, False, None)
  def test_create_vf_flag(self, flag):
    """Check is_verification_needed flag setup on create."""
    data = self.get_workflow_dict()
    if flag is None:
      data['workflow'].pop('is_verification_needed', None)
    else:
      data['workflow']['is_verification_needed'] = flag
    resp = self.api.post(all_models.Workflow, data)
    self.assertEqual(201, resp.status_code)
    workflow_id = resp.json['workflow']['id']
    self.assertEqual(
        flag if flag is not None else True,
        all_models.Workflow.query.get(workflow_id).is_verification_needed)
