# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Initialize application with ggrc_wokflows_new blueprint's models."""
from ggrc.models import all_models
from ggrc_workflows_new.models import workflow_new


all_models.register_model(workflow_new.WorkflowNew)
