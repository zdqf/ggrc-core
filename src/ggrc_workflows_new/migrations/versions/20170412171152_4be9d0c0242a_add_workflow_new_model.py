# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Add table for WorkflowNew model.

Create Date: 2017-04-03 12:00:05.686115
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name, duplicate-code

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4be9d0c0242a'
down_revision = None

table_name = 'workflows_new'


DAY_UNIT = u'Day'
MONTH_UNIT = u'Month'


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  op.create_table(
      table_name,
      sa.Column('slug', sa.String(length=250), nullable=False),
      sa.Column('modified_by_id', sa.Integer()),
      sa.Column('created_at', sa.DateTime(), nullable=False),
      sa.Column('updated_at', sa.DateTime(), nullable=False),
      sa.Column('context_id', sa.Integer(), sa.ForeignKey('contexts.id')),
      sa.Column('id', sa.Integer(), primary_key=True),
      sa.Column('description', sa.Text()),
      sa.Column('title', sa.String(length=250), nullable=False),
      sa.Column('repeat_every', sa.Integer()),
      sa.Column('unit', sa.Enum(DAY_UNIT, MONTH_UNIT)),
      sa.Column('parent_id', sa.Integer(),
                sa.ForeignKey('{}.id'.format(table_name)))
  )
  op.create_unique_constraint('uq_{}'.format(table_name), table_name, ["slug"])
  op.create_index('ix_{}_updated_at'.format(table_name), table_name,
                  ['updated_at'])
  op.create_index('fk_{}_contexts'.format(table_name), table_name,
                  ['context_id'])
  op.create_index('fk_{}_parent_id'.format(table_name), table_name,
                  ['parent_id'])


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.drop_table(table_name)
