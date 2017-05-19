# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module contains main functions for workflows_new blueprint."""
# pylint: disable=too-few-public-methods
from datetime import datetime
import flask
import sqlalchemy as sa
from ggrc import db
from ggrc import login
from ggrc.services import common
from ggrc.services import registry as registry_service
from ggrc.views import registry as registry_view
from ggrc_basic_permissions import contributed_roles
from ggrc_basic_permissions import models as permission_models
from ggrc_workflows_new.models import label as label_module
from ggrc_workflows_new.models import task as task_module
from ggrc_workflows_new.models import task_comment
from ggrc_workflows_new.models import workflow_new
from ggrc_workflows_new.models import workflow_person_new
from ggrc_workflows_new.roles import BasicWorkflowReaderNew
from ggrc_workflows_new.roles import WorkflowBasicReaderNew
from ggrc_workflows_new.roles import WorkflowMemberNew
from ggrc_workflows_new.roles import WorkflowOwnerNew


blueprint = flask.Blueprint('ggrc_workflows_new', __name__)  # noqa # pylint: disable=invalid-name


def contributed_services():
  """Return contributed object services."""
  return (
      registry_service.service('workflows_new', workflow_new.WorkflowNew),
      registry_service.service('tasks', task_module.Task),
      registry_service.service('task_comments', task_comment.TaskComment),
      registry_service.service('workflow_people_new',
                               workflow_person_new.WorkflowPersonNew),
  )


def contributed_object_views():
  """Return contributed object views."""
  return (
      registry_view.object_view(workflow_new.WorkflowNew),
  )


@common.Resource.model_posted.connect_via(workflow_new.WorkflowNew)
def handle_workflow_new_post(sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  """Handle WorkflowNew model POST."""
  _validate_is_template_workflow(obj)
  user = login.get_current_user()
  personal_context = user.get_or_create_object_context(
      context=1,
      name='Personal Context for {0}'.format(user.id),
      description='',
  )
  personal_context.modified_by = user
  db.session.add(personal_context)
  db.session.flush()

  context = obj.build_object_context(
      context=personal_context,
      name='{object_type} Context {timestamp}'.format(
          object_type=service.model.__name__,
          timestamp=datetime.now()
      ),
      description='',
  )
  context.modified_by = user
  db.session.add(obj)
  db.session.flush()
  db.session.add(context)
  db.session.flush()
  obj.contexts.append(context)
  obj.context = context

  workflow_owner_role = _find_role('WorkflowOwnerNew')
  user_role = permission_models.UserRole(
      person=user,
      role=workflow_owner_role,
      context=context,
      modified_by=user,
  )
  db.session.add(user_role)
  workflow_owner = workflow_person_new.WorkflowPersonNew(
      person=user,
      workflow=obj,
      context=context,
      modified_by=user,
  )
  db.session.add(workflow_owner)
  db.session.flush()

  db.session.add(permission_models.ContextImplication(
      source_context=context,
      context=None,
      source_context_scope='WorkflowNew',
      context_scope=None,
      modified_by=user,
  ))

  db.session.add(permission_models.ContextImplication(
      source_context=None,
      context=context,
      source_context_scope=None,
      context_scope='WorkflowNew',
      modified_by=user,
  ))
  _generate_cycle(obj)


@common.Resource.model_put.connect_via(workflow_new.WorkflowNew)
def handle_workflow_put(sender, obj, src=None, service=None):  # noqa pylint: disable=unused-argument
  """Handle WorkflowNew model PUT."""
  _validate_is_template_workflow(obj)


@common.Resource.model_posted.connect_via(
    workflow_person_new.WorkflowPersonNew)
def handle_workflow_person_post(sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  """Handle WorkflowPersonNew model POST."""
  user_role = permission_models.UserRole(
      person=obj.person,
      role=_find_role('WorkflowMemberNew'),
      context=obj.context,
      modified_by=login.get_current_user(),
  )
  db.session.add(user_role)
  db.session.flush()


@common.Resource.model_posted.connect_via(task_module.Task)
def handle_task_post(sender, obj, src=None, service=None):  # noqa pylint: disable=unused-argument
  """Handle Task model POST."""
  _validate_is_cycle_task(obj)
  _validate_cycle_task_status(obj)
  _ensure_assignee_is_workflow_member(obj)
  _setup_cycle_task_label(obj, src['label_title'])
  if src['is_update_template']:
    _generate_task(obj)


@common.Resource.model_put.connect_via(task_module.Task)
def handle_task_put(sender, obj, src=None, service=None):  # noqa pylint: disable=unused-argument
  """Handle Task model PUT."""
  _validate_is_cycle_task(obj)
  if sa.inspect(obj).attrs.contact.history.has_changes():
    _ensure_assignee_is_workflow_member(obj)
  old_label = obj.label
  if old_label.title != src['label_title']:
    _setup_cycle_task_label(obj, src['label_title'])
  if src['is_update_template']:
    if obj.parent:
      _update_cycle_task_template(obj)
    else:
      _generate_task(obj)
  if old_label.title != src['label_title']:
    _delete_orphan_label(old_label)


@common.Resource.model_deleted.connect_via(task_module.Task)
def handle_task_delete(sender, obj, src=None, service=None):  # noqa pylint: disable=unused-argument
  """Handle Task model DELETE."""
  _delete_orphan_label(obj.label, exclude_task=obj)


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


def _generate_cycle(workflow_template):
  cycle = workflow_new.WorkflowNew(
      context=workflow_template.context,
      parent=workflow_template
  )
  db.session.add(cycle)
  for task_template in workflow_template.tasks:
    _generate_task(task_template)
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


def _validate_is_template_workflow(workflow):
  if not workflow.is_template:
    raise ValueError(u"Can't send POST/PUT requests for cycle")


def _validate_is_cycle_task(task):
  if task.is_template:
    raise ValueError(u"Can't send POST/PUT requests for template task")


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


def _find_role(role_name):
  return db.session.query(permission_models.Role).filter(
      permission_models.Role.name == role_name).first()


class WorkflowRoleContributionsNew(contributed_roles.RoleContributions):
  contributions = {
      'ProgramCreator': {
          'read': ['WorkflowNew'],
          'create': ['WorkflowNew'],
      },
      'Creator': {
          'create': ['WorkflowNew', 'Task']
      },
      'Editor': {
          'read': ['WorkflowNew', 'Task'],
          'create': ['WorkflowNew', 'Task'],
          'update': ['Task'],
          'edit': ['Task'],
          'delete': ['Task']
      },
      'Reader': {
          'read': ['WorkflowNew', 'Task'],
          'create': ['WorkflowNew', 'Task'],
      },
      'ProgramEditor': {
          'read': ['WorkflowNew'],
          'create': ['WorkflowNew'],
      },
      'ProgramOwner': {
          'read': ['WorkflowNew'],
          'create': ['WorkflowNew'],
      },
  }


class WorkflowRoleDeclarationsNew(contributed_roles.RoleDeclarations):
  def roles(self):
    return {
        'WorkflowOwnerNew': WorkflowOwnerNew,
        'WorkflowMemberNew': WorkflowMemberNew,
        'BasicWorkflowReaderNew': BasicWorkflowReaderNew,
        'WorkflowBasicReaderNew': WorkflowBasicReaderNew,
    }


class WorkflowRoleImplicationsNew(
        contributed_roles.DeclarativeRoleImplications):
  implications = {
      (None, 'WorkflowNew'): {
          'ProgramCreator': ['BasicWorkflowReaderNew'],
          'Editor': ['WorkflowOwnerNew'],
          'Reader': ['BasicWorkflowReaderNew'],
          'Creator': ['WorkflowBasicReaderNew'],
      },
      ('WorkflowNew', None): {
          'WorkflowOwnerNew': ['WorkflowBasicReaderNew'],
          'WorkflowMemberNew': ['WorkflowBasicReaderNew'],
      },
  }

ROLE_CONTRIBUTIONS = WorkflowRoleContributionsNew()
ROLE_DECLARATIONS = WorkflowRoleDeclarationsNew()
ROLE_IMPLICATIONS = WorkflowRoleImplicationsNew()
