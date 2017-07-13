# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module contains main functions for ggrc_workflows_new blueprint."""
# pylint: disable=too-few-public-methods
import flask
from ggrc import db
from ggrc.services import registry as registry_service
from ggrc.views import registry as registry_view
from ggrc.services import signals
from ggrc_workflows_new.models import task as task_module
from ggrc_workflows_new.models import workflow_template


blueprint = flask.Blueprint('ggrc_workflows_new', __name__)  # noqa # pylint: disable=invalid-name


def contributed_services():
  """Return contributed object services."""
  return (
      registry_service.service('workflow_templates', workflow_template.WorkflowTemplate),
      registry_service.service('tasks', task_module.Task),
  )


def contributed_object_views():
  """Return contributed object views."""
  return (
      registry_view.object_view(workflow_template.WorkflowTemplate),
  )


@signals.Restful.model_posted.connect_via(workflow_template.WorkflowTemplate)
def handle_workflow_template_post(sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  """Handle WorkflowNew model POST."""
  pass


@signals.Restful.model_put.connect_via(workflow_template.WorkflowTemplate)
def handle_workflow_put(sender, obj, src=None, service=None):  # noqa pylint: disable=unused-argument
  """Handle WorkflowNew model PUT."""
  pass


def _generate_task(task):
  """Generate task.

  task: if this argument is Task Template then we generate Cycle Task
        if this argument is Cycle Task then we generate Template Task
  """
  new_task_status = (task.NOT_STARTED_STATUS
                     if task.is_template else task.TEMPLATE_STATUS)
  new_task_workflow = (task.workflow
                       if task.is_template else task.worlflow.parent)
  new_task = task_module.Task(
      title=task.title,
      description=task.description,
      contact=task.contact,
      start_date=task.start_date,
      end_date=task.end_date,
      workflow=new_task_workflow,
      status=new_task_status,
      label=task.label,
      parent=None,
      context=task.context
  )
  if task.is_template:
    new_task.parent = task
    db.session.add(new_task)
  else:
    db.session.add(new_task)
    task.parent = new_task
    db.session.add(task)
  db.session.flush()


def _update_cycle_task_template(cycle_task):
  is_template_changed = False
  for attr_name in cycle_task.UPDATE_TEMPLATE_ATTRS:
    if getattr(cycle_task.parent, attr_name) != getattr(cycle_task, attr_name):
      setattr(cycle_task.parent, attr_name, getattr(cycle_task, attr_name))
      is_template_changed = True
  if is_template_changed:
    db.session.add(cycle_task.parent)
    db.session.flush()


def _validate_cycle_task_status(cycle_task):
  """Make sure that Task's status value is valid.

  It was moved from SQLAlchemy validator because this attribute depends from
  'workflow' attribute. When task object is posted 'status' validator needs
  that 'workflow' attribute has been already set.

  Args:
      cycle_task: Task model instance.

  Raises:
      ValueError: An error occurred when invalid status set to 'task.status'.
  """
  if cycle_task.status not in cycle_task.VALID_STATUSES:
    raise ValueError(u"Task invalid status: '{}'".format(cycle_task.status))
  if cycle_task.status not in cycle_task.NON_TEMPLATE_STATUSES:
    raise ValueError(
        u"Non-template task must have one of the statuses: "
        u"'{}'".format(', '.join(cycle_task.NON_TEMPLATE_STATUSES)))
