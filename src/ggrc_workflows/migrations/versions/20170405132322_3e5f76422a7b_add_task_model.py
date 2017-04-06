# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Add task model.

Create Date: 2017-04-05 13:23:22.022321
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision = '3e5f76422a7b'
down_revision = '9a69ccb4035'

table_name = 'tasks'


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  op.create_table(
      table_name,
      sa.Column('description', sa.Text()),
      sa.Column('title', sa.String(length=250), nullable=False),
      sa.Column('slug', sa.String(length=250), nullable=False),
      sa.Column('modified_by_id', sa.Integer()),
      sa.Column('created_at', sa.DateTime(), nullable=False),
      sa.Column('updated_at', sa.DateTime(), nullable=False),
      sa.Column('context_id', sa.Integer(), sa.ForeignKey('contexts.id')),
      sa.Column('id', sa.Integer(), primary_key=True),
      sa.Column('contact_id', sa.Integer(), sa.ForeignKey('people.id')),
      sa.Column('status', sa.String(length=250), nullable=False),
      sa.Column('start_date', sa.Date(), nullable=False),
      sa.Column('end_date', sa.Date(), nullable=False),
      sa.Column('workflow_id', sa.Integer(),
                sa.ForeignKey('workflows_new.id'), nullable=False),
  )
  op.create_unique_constraint('uq_{}'.format(table_name), table_name, ["slug"])
  op.create_index('ix_{}_updated_at'.format(table_name), table_name,
                  ['updated_at'])
  op.create_index('fk_{}_contexts'.format(table_name), table_name,
                  ['context_id'])
  op.create_index('fk_{}_contact'.format(table_name), table_name,
                  ['contact_id'])


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.drop_table(table_name)
