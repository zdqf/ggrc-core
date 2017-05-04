# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Initialize application with ggrc_wokflows_new blueprint's models."""
from ggrc.models import all_models
from ggrc_workflows_new.models import label
from ggrc_workflows_new.models import task
from ggrc_workflows_new.models import workflow_new
from ggrc_workflows_new.models import workflow_person_new


all_models.register_model(label.Label)
all_models.register_model(task.Task)
all_models.register_model(workflow_new.WorkflowNew)
all_models.register_model(workflow_person_new.WorkflowPersonNew)
