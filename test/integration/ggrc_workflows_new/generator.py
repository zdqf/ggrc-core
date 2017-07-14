# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
Set of generators for Workflow related models
"""

import copy

from ggrc.models import all_models
from integration.ggrc.generator import Generator
from integration.ggrc.models import factories


class WorkflowGenerator(Generator):

  def generate_workflow(self, data=None):
    """ create a workflow with dict data
    return: wf if it was created, or response otherwise
    """
    if not data:
      data = {}
    obj_name = "workflowtemplate"
    data = copy.deepcopy(data)

    wflow = all_models.WorkflowTemplate(title="wf " + factories.random_str())
    obj_dict = self.obj_to_dict(wflow, obj_name)
    obj_dict[obj_name].update(data)

    response, workflow = self.generate(all_models.WorkflowTemplate,
                                       obj_name, obj_dict)

    return response, workflow
