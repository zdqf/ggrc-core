# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
Create WorkflowNew's people table.

Create Date: 2017-04-26 14:03:17.264561
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: skip-file
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '21628bac2031'
down_revision = '1a5628c528f9'
TABLE_NAME = 'workflow_people_new'


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  op.create_table(
      TABLE_NAME,
      sa.Column('modified_by_id', sa.Integer()),
      sa.Column('created_at', sa.DateTime(), nullable=False),
      sa.Column('updated_at', sa.DateTime(), nullable=False),
      sa.Column('context_id', sa.Integer()),
      sa.Column('id', sa.Integer(), primary_key=True),
      sa.Column('workflow_id', sa.Integer(), nullable=False),
      sa.Column('person_id', sa.Integer(), nullable=False),
      sa.ForeignKeyConstraint(['context_id'], ['contexts.id'],
                              'fk_workflow_people_new_context_id'),
      sa.ForeignKeyConstraint(['workflow_id'], ['workflows_new.id'],
                              'fk_workflow_people_new_workflow_new_id',
                              ondelete='CASCADE'),
      sa.ForeignKeyConstraint(['person_id'], ['people.id'],
                              'fk_workflow_people_new_people_id'),
  )
  op.create_index('ix_{}_updated_at'.format(TABLE_NAME), TABLE_NAME,
                  ['updated_at'])
  op.create_index('fk_{}_contexts'.format(TABLE_NAME), TABLE_NAME,
                  ['context_id'])
  op.create_index('fk_{}_workflow_id'.format(TABLE_NAME), TABLE_NAME,
                  ['workflow_id'])
  op.create_index('fk_{}_person_id'.format(TABLE_NAME), TABLE_NAME,
                  ['person_id'])


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.drop_table(TABLE_NAME)
