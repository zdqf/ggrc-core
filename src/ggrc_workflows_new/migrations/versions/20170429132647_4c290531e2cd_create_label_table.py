# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
Create table for Label model

Create Date: 2017-04-29 13:26:47.915613
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: skip-file
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c290531e2cd'
down_revision = '21628bac2031'
TABLE_NAME = 'labels'


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  op.create_table(
      TABLE_NAME,
      sa.Column('title', sa.String(length=250), nullable=False),
      sa.Column('modified_by_id', sa.Integer()),
      sa.Column('created_at', sa.DateTime(), nullable=False),
      sa.Column('updated_at', sa.DateTime(), nullable=False),
      sa.Column('context_id', sa.Integer()),
      sa.Column('id', sa.Integer(), primary_key=True),
      sa.Column('workflow_id', sa.Integer(), nullable=False),
      sa.ForeignKeyConstraint(['context_id'], ['contexts.id'],
                              'fk_label_context_id'),
      sa.ForeignKeyConstraint(['workflow_id'], ['workflows_new.id'],
                              'fk_label_workflow_new_id', ondelete='CASCADE')
  )
  op.create_index('ix_{}_updated_at'.format(TABLE_NAME), TABLE_NAME,
                  ['updated_at'])
  op.create_index('fk_{}_contexts'.format(TABLE_NAME), TABLE_NAME,
                  ['context_id'])
  op.create_index('fk_{}_workflow'.format(TABLE_NAME), TABLE_NAME,
                  ['workflow_id'])

  # Create foreign key/index constraints between task and label table
  op.add_column('tasks', sa.Column('label_id', sa.Integer()))
  op.create_foreign_key("fk_task_label_id", "tasks", "labels", ["label_id"],
                        ["id"])
  op.create_index('fk_{}_label'.format('tasks'), 'tasks', ['label_id'])

def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.drop_table(TABLE_NAME)
