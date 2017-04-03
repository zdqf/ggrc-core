# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
Add table for WorkflowNew model

Create Date: 2017-04-03 12:00:05.686115
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a69ccb4035'
down_revision = '1142135ce819'

table_name = 'workflows_new'


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  op.create_table(
    table_name,
    sa.Column('slug', sa.String(length=250), nullable=False),
    sa.Column('modified_by_id', sa.Integer()),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
  )
  op.create_unique_constraint('uq_{}'.format(table_name), table_name, ["slug"])
  op.create_index('ix_{}_updated_at'.format(table_name), table_name,
                  ['updated_at'])


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.drop_table(table_name)
