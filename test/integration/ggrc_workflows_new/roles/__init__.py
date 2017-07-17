# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Test how different roles can access Workflow specific object"""

from ggrc import db
from integration.ggrc_workflows_new import WorkflowTestCase


class WorkflowRolesTestCase(WorkflowTestCase):
  """Workflow roles test case"""

  def setUp(self):
    super(WorkflowRolesTestCase, self).setUp()

    self.workflow_res = None
    self.workflow_obj = None

    self.users = {}

    self.session = db.session
    self.init_users()
    self.random_objects = self.object_generator.generate_random_objects()
    self.init_workflow()

  def init_users(self):
    """Initializes users needed by the test"""

    users = [
        ("creator", "Creator"),
        ("reader", "Reader"),
        ("editor", "Editor"),
        ("admin", "Administrator"),
        ("admin2", "Administrator")
    ]
    for (name, role) in users:
      _, user = self.object_generator.generate_person(
          data={"name": name}, user_role=role)
      self.users[name] = user

  def init_workflow(self, data=None):
    """Creates a workflow which is owned by an user with Admin role"""

    initial_workflow_data = {
        "latest_cycle_number": 1,
        "description": "",
        "slug": "WORKFLOWTEMPLATE-11",
        "unit": None,
        "archived": False,
        "title": "sfsf",
        "repeat_every": None,
        "type": "WorkflowTemplate",
    }
    if data:
      initial_workflow_data.update(data)

    self.workflow_res, self.workflow_obj =\
        self.generator.generate_workflow(initial_workflow_data)
    self.assertEqual(201, self.workflow_res.status_code)
