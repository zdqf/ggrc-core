# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

# pylint: disable=too-few-public-methods,missing-docstring,old-style-class
# pylint: disable=no-init


from ggrc.models import all_models
from integration.ggrc.models.factories import TitledFactory


class WorkflowFactory(TitledFactory):

  class Meta:
    model = all_models.WorkflowTemplate
