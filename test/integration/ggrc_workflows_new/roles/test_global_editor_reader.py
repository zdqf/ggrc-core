# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
Test if global editor and global reader role has the permission to access
the workflow objects, owned by Admin.
"""

from appengine.base import with_memcache
from ggrc.models import all_models

from integration.ggrc_workflows_new.roles import WorkflowRolesTestCase


@with_memcache
class GlobalEditorReaderGetTest(WorkflowRolesTestCase):
  """ Get workflow objects owned by another user
  as global editor and global reader.
  """

  def assert200_helper(self, response, message=None):
    """Helper that adds the info of the current user to the message.
    """
    message = message or \
        "Requests as user: '{}' Response returned {} instead of 200."\
        .format(self.api.person_name, response.status_code)
    self.assert200(response, message)

  def test_get_obj_as_editor(self):
    """ Get workflow object from draft workflow as a editor """
    self._get_workflow_objects(self.users['editor'])

  def test_get_obj_as_reader(self):
    """ Get workflow object from draft workflow as a reader """
    self._get_workflow_objects(self.users['reader'])

  def _get_workflow_objects(self, user):
    """ Helper method that runs tests for draft workflow
    Args:
       user: Person object
    """

    self.api.set_user(user)
    workflow_res = self.api.get(all_models.WorkflowTemplate,
                                self.workflow_obj.id)
    self.assert200_helper(workflow_res)
