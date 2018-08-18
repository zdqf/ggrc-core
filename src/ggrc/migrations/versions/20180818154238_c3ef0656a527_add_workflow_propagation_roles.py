# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
add workflow propagation roles

Create Date: 2018-08-18 15:42:38.059053
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

import datetime

from alembic import op

from ggrc.migrations.utils import acr_propagation
from ggrc.migrations.utils import acr_propagation_constants_workflows as const


# revision identifiers, used by Alembic.
revision = 'c3ef0656a527'
down_revision = 'ace8f9834418'


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  acr_propagation.propagate_roles(const.WORKFLOW_PROPAGATION)
  op.execute(
      acr_propagation.ACR_TABLE.delete().where(
          acr_propagation.ACR_TABLE.c.name.in_([
              'Admin Mapped',
              'Workflow Member Mapped',
          ])
      )
  )


def downgrade():
  """Remove Risk propagated roles"""
  for object_type, roles_tree in const.WORKFLOW_PROPAGATION.items():
    acr_propagation.remove_propagated_roles(object_type, roles_tree.keys())

  op.bulk_insert(
      acr_propagation.ACR_TABLE,
      [{
          'name': 'Admin Mapped',
          'object_type': 'Workflow',
          'tooltip': None,
          'read': True,
          'update': True,
          'delete': True,
          'my_work': False,
          'mandatory': False,
          'non_editable': True,
          'internal': True,
          'created_at': datetime.datetime.now(),
          'updated_at': datetime.datetime.now(),
          'default_to_current_user': False,
      }, {
          'name': 'Workflow Member Mapped',
          'object_type': 'Workflow',
          'tooltip': None,
          'read': True,
          'update': False,
          'delete': False,
          'my_work': False,
          'mandatory': False,
          'non_editable': True,
          'internal': True,
          'created_at': datetime.datetime.now(),
          'updated_at': datetime.datetime.now(),
          'default_to_current_user': False,
      }]
  )
