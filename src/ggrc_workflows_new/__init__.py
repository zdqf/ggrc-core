# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module contains main functions for ggrc_workflows_new blueprint."""
# pylint: disable=too-few-public-methods
from datetime import datetime
import flask
import sqlalchemy as sa
from ggrc import db
from ggrc import login
from ggrc.services import registry as registry_service
from ggrc.views import registry as registry_view
from ggrc.services import signals
from ggrc_basic_permissions import contributed_roles
from ggrc_basic_permissions import models as permission_models
from ggrc_workflows_new.models import label as label_module
from ggrc_workflows_new.models import task as task_module
from ggrc_workflows_new.models import task_comment
from ggrc_workflows_new.models import workflow_template
from ggrc_workflows_new.models import workflow_person_new
from ggrc_workflows_new.roles import BasicWorkflowReaderNew
from ggrc_workflows_new.roles import WorkflowBasicReaderNew
from ggrc_workflows_new.roles import WorkflowMemberNew
from ggrc_workflows_new.roles import WorkflowOwnerNew


blueprint = flask.Blueprint('ggrc_workflows_new', __name__)  # noqa # pylint: disable=invalid-name


def contributed_services():
  """Return contributed object services."""
  return (
      registry_service.service('workflow_templates', workflow_template.WorkflowTemplate),
      registry_service.service('tasks', task_module.Task),
      registry_service.service('task_comments', task_comment.TaskComment),
      registry_service.service('workflow_people_new',
                               workflow_person_new.WorkflowPersonNew),
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


def _setup_cycle_task_label(cycle_task, label_title):
  for label in cycle_task.workflow.parent.labels:
    if label.title == label_title:
      break
  else:
    label = label_module.Label(
        title=label_title,
        workflow=cycle_task.workflow.parent,
        context=cycle_task.workflow.parent.context
    )
    db.session.add(label)
  cycle_task.label = label
  db.session.add(cycle_task)
  db.session.flush()


def _delete_orphan_label(label, exclude_task=None):
  if not label.tasks or (exclude_task and len(label.tasks) == 1 and
                         exclude_task in label.tasks):
    db.session.delete(label)
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


def _ensure_assignee_is_workflow_member(cycle_task):  # noqa pylint: disable=invalid-name
  """Ensure that assignee has role WorkflowMember.

  Args:
    workflow: Parent WorkflowNew object for task model.
    assignee: Person object setup for task model.
  """
  is_assignee_in_template = False
  for wp in cycle_task.workflow.parent.workflow_people:
    if cycle_task.contact == wp.person:
      is_assignee_in_template = True
      break
  if not is_assignee_in_template:
    workflow_member = workflow_person_new.WorkflowPersonNew(
        person=cycle_task.contact,
        workflow=cycle_task.workflow.parent,
        context=cycle_task.workflow.parent.context
    )
    db.session.add(workflow_member)
    user_role = permission_models.UserRole(
        person=cycle_task.contact,
        role=_find_role('WorkflowMemberNew'),
        context=cycle_task.workflow.parent.context,
        modified_by=login.get_current_user(),
    )
    db.session.add(user_role)
    db.session.flush()
