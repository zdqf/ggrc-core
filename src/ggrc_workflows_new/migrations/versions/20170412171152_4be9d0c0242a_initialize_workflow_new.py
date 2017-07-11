# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
Initialize data needed for workflow-new feature.

Create Date: 2017-04-03 12:00:05.686115
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '4be9d0c0242a'
down_revision = None
WT_TABLE_NAME = 'workflow_templates'
WT_DAY_UNIT = u'Day'
WT_WEEK_UNIT = u'Week'
WT_MONTH_UNIT = u'Month'


acr_table = sa.sql.table('access_control_roles',
                         sa.sql.column('id', sa.Integer),
                         sa.sql.column('name', sa.String),
                         sa.sql.column('object_type', sa.String),
                         sa.sql.column('tooltip'),
                         sa.sql.column('read', sa.Boolean),
                         sa.sql.column('update', sa.Boolean),
                         sa.sql.column('delete', sa.Boolean),
                         sa.sql.column('my_work', sa.Boolean),
                         sa.sql.column('created_at', sa.DateTime),
                         sa.sql.column('modified_by_id', sa.Integer),
                         sa.sql.column('updated_at', sa.DateTime),
                         sa.sql.column('context_id', sa.Integer),
                         sa.sql.column('mandatory', sa.Boolean),
                        )

def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  op.create_table(
      WT_TABLE_NAME,
      sa.Column('archived', sa.Boolean(), nullable=False, server_default="0"),
      sa.Column('context_id', sa.Integer()),
      sa.Column('created_at', sa.DateTime(), nullable=False),
      sa.Column('description', sa.Text()),
      sa.Column('id', sa.Integer(), primary_key=True),
      sa.Column('latest_cycle_number', sa.Integer(), nullable=False, server_default="1"),
      sa.Column('modified_by_id', sa.Integer()),
      sa.Column('occurrences', sa.Integer()),
      sa.Column('repeat_every', sa.Integer()),
      sa.Column('slug', sa.String(length=250), nullable=False),
      sa.Column('title', sa.String(length=250), nullable=False),
      sa.Column('unit', sa.Enum(WT_DAY_UNIT, WT_WEEK_UNIT, WT_MONTH_UNIT)),
      sa.Column('updated_at', sa.DateTime(), nullable=False),
      sa.ForeignKeyConstraint(['context_id'], ['contexts.id'],
                              'fk_workflow_template_context_id'),
  )
  op.create_unique_constraint('uq_{}'.format(WT_TABLE_NAME), WT_TABLE_NAME, ["slug"])
  op.create_index('ix_{}_updated_at'.format(WT_TABLE_NAME), WT_TABLE_NAME,
                  ['updated_at'])

  # Insert ACR values needed for WorkflowTemplate model
  op.bulk_insert(acr_table,
                 [
                   {
                     'name': 'Admin',
                     'object_type': 'WorkflowTemplate',
                     'read': True,
                     'update': True,
                     'delete': True,
                     'created_at': datetime.now(),
                     'updated_at': datetime.now(),
                     'mandatory': True
                   },
                   {
                     'name': 'CC List',
                     'object_type': 'WorkflowTemplate',
                     'read': True,
                     'update': False,
                     'delete': False,
                     'created_at': datetime.now(),
                     'updated_at': datetime.now(),
                     'mandatory': False
                   },
                 ])


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.drop_table(WT_TABLE_NAME)
  op.execute(acr_table.delete().where(acr_table.c.name.in_(
    [
      op.inline_literal('Admin'),
      op.inline_literal('CC List')
    ]))
  )
