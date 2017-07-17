# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
Test if global creator role has the permission to access the workflow objects,
owned by Admin.
"""

from ggrc.models import all_models

from integration.ggrc_workflows_new.roles import WorkflowRolesTestCase


class GlobalCreatorGetTest(WorkflowRolesTestCase):
  """ Get workflow objects owned by another user as global creator.
  """

  def setUp(self):
    super(GlobalCreatorGetTest, self).setUp()
    self.api.set_user(self.users['creator'])

  def test_gc_create_wf(self):
    """ Get Creator can create WF """
    wf_data = {
        "slug": "test_gc_create_wf-1",
        "title": "test_gc_create_wf",
    }
    self.init_workflow(wf_data)

  def test_get_obj(self):
    """ Get workflow objects from draft workflow """
    workflow_res = self.api.get(all_models.WorkflowTemplate,
                                self.workflow_obj.id)
    self.assert403(workflow_res)
