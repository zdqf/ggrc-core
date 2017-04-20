# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Module contains main functions for workflows_new blueprint."""
# pylint: disable=too-few-public-methods
from datetime import datetime
import flask
from ggrc import db
from ggrc import login
from ggrc.services import common
from ggrc.services import registry as registry_service
from ggrc.views import registry as registry_view
from ggrc_basic_permissions import contributed_roles
from ggrc_basic_permissions import models as permission_models
from ggrc_workflows_new.models import workflow_new
from ggrc_workflows_new.roles import BasicWorkflowReaderNew
from ggrc_workflows_new.roles import WorkflowBasicReaderNew
from ggrc_workflows_new.roles import WorkflowMemberNew
from ggrc_workflows_new.roles import WorkflowOwnerNew


blueprint = flask.Blueprint('ggrc_workflows_new', __name__)  # noqa # pylint: disable=invalid-name


def contributed_services():
  """Return contributed object services."""
  return (
      registry_service.service('workflows_new', workflow_new.WorkflowNew),
  )


def contributed_object_views():
  """Return contributed object views."""
  return (
      registry_view.object_view(workflow_new.WorkflowNew),
  )


def _find_role(role_name):
  return db.session.query(permission_models.Role).filter(
      permission_models.Role.name == role_name).first()


@common.Resource.model_posted.connect_via(workflow_new.WorkflowNew)
def handle_workflow_new_post(sender, obj=None, src=None, service=None):  # noqa pylint: disable=unused-argument
  """Handle WorkflowNew model POST."""
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
