# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
create workflow roles

Create Date: 2017-04-19 20:47:44.416821
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from datetime import datetime
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a5628c528f9'
down_revision = '55b30bba8230'


roles_table = sa.sql.table(
    'roles',
    sa.sql.column('id', sa.Integer),
    sa.sql.column('name', sa.String),
    sa.sql.column('permissions_json', sa.Text),
    sa.sql.column('description', sa.Text),
    sa.sql.column('modified_by_id', sa.Integer),
    sa.sql.column('created_at', sa.DateTime),
    sa.sql.column('updated_at', sa.DateTime),
    sa.sql.column('context_id', sa.Integer),
    sa.sql.column('scope', sa.String),
    sa.sql.column('role_order', sa.Integer),
)


WORKFLOW_ROLES = (
    ('WorkflowOwnerNew', 'WorkflowNew'),
    ('WorkflowMemberNew', 'WorkflowNew'),
    ('BasicWorkflowReaderNew', 'WorkflowNew Implied'),
    ('WorkflowBasicReaderNew', 'WorkflowNew Implied'),
)


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  current_datetime = datetime.now()
  values = []
  for name, scope in WORKFLOW_ROLES:
    values.append(dict(
        name=name,
        permissions_json='CODE DECLARED ROLE',
        description=' ',
        modified_by_id=1,
        created_at=current_datetime,
        updated_at=current_datetime,
        context_id=None,
        scope=scope,
        role_order=None
    ))
  op.execute(roles_table.insert().values(values))


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  names = (val[0] for val in WORKFLOW_ROLES)
  op.execute(roles_table.delete().where(roles_table.c.name.in_(names)))
