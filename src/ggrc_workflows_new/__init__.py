# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module contains main functions for workflows_new blueprint."""
import flask
from ggrc.services import registry
from ggrc_workflows_new.models import workflow_new


blueprint = flask.Blueprint('ggrc_workflows_new', __name__)  # noqa # pylint: disable=invalid-name


def contributed_services():
  return (
      registry.service('workflows_new', workflow_new.WorkflowNew),
  )
