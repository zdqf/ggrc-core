# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
Tests for interaction with Workflows via api calls
"""

from ggrc.models import all_models

from integration.ggrc import TestCase
from integration.ggrc.api_helper import Api
from integration.ggrc.models import factories
from integration.ggrc_workflows_new.models import factories as wf_factories


class TestWorkflowsApi(TestCase):
  """
  Test Workflows api
  """
  def setUp(self):
    super(TestWorkflowsApi, self).setUp()
    self.api = Api()

  def tearDown(self):
    pass

  def test_send_invalid_data(self):
    """Test wf not created"""
    data = self.get_workflow_dict()
    del data["workflow_template"]["title"]
    response = self.api.post(all_models.WorkflowTemplate, data)
    self.assertNotEqual(response.status_code, 201)
    # TODO: check why response.json["message"] is empty

  def test_create_basic_workflow(self):
    """Test wf created"""
    data = self.get_workflow_dict()
    response = self.api.post(all_models.WorkflowTemplate, data)
    self.assertEqual(response.status_code, 201)

  def test_create_weekly_workflows(self):
    """Test weekly wf created"""
    data = self.get_workflow_dict()
    data["workflow_template"]["unit"] = "Week"
    data["workflow_template"]["repeat_every"] = 1
    data["workflow_template"]["title"] = "Test weekly workflow"
    response = self.api.post(all_models.WorkflowTemplate, data)
    self.assertEqual(response.status_code, 201)

  def test_create_monthly_workflows(self):
    """Test monthly wf created"""
    data = self.get_workflow_dict()
    data["workflow_template"]["frequency"] = "monthly"
    data["workflow_template"]["title"] = "Monthly"
    response = self.api.post(all_models.WorkflowTemplate, data)
    self.assertEqual(response.status_code, 201)

  def test_change_workflow_data(self):
    """Check 'repeat_every' field changed."""
    with factories.single_commit():
      workflow = wf_factories.WorkflowFactory()
    workflow_id = workflow.id
    self.assertNotEqual(
        5,
        all_models.WorkflowTemplate.query.get(workflow_id).repeat_every)
    resp = self.api.put(workflow, {"repeat_every": 5,
                                   "unit": "Day"})
    self.assert200(resp)
    self.assertEqual(
        5,
        all_models.WorkflowTemplate.query.get(workflow_id).repeat_every)

  def test_delete_workflow(self):
    """Check workflow deleted over api."""
    with factories.single_commit():
      workflow = wf_factories.WorkflowFactory()
    workflow_id = workflow.id
    self.assertNotEqual(
        None,
        all_models.WorkflowTemplate.query.get(workflow_id))
    resp = self.api.delete(workflow)
    self.assert200(resp)
    self.assertEqual(
        None,
        all_models.WorkflowTemplate.query.get(workflow_id))

  @staticmethod
  def get_workflow_dict():
    """Basic workflow_template data"""
    data = {
        "workflow_template": {
            "context": {"id": None},
            "title": "Test daily workflow",
            "slug": "WORKFLOWTEMPLATE-11",
            "description": "",
            "repeat_every": 1,
            "unit": "Day",
            "archived": False,
            "latest_cycle_number": 1,
            "occurrences": None,
        }
    }
    return data
