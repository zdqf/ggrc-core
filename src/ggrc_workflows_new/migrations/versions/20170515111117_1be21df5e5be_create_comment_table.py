# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
Create comments table

Create Date: 2017-05-15 11:11:17.213581
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '1be21df5e5be'
down_revision = '4c290531e2cd'
TABLE_NAME = 'task_comments'


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  op.create_table(
    TABLE_NAME,
    sa.Column('description', sa.Text()),
    sa.Column('modified_by_id', sa.Integer()),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('context_id', sa.Integer()),
    sa.Column('id', sa.Integer(), primary_key=True),
    sa.Column('task_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['context_id'], ['contexts.id'],
                            'fk_task_comment_context_id'),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'],
                            'fk_task_comment_task_id', ondelete='CASCADE'),
  )
  op.create_index('ix_{}_updated_at'.format(TABLE_NAME), TABLE_NAME,
                  ['updated_at'])
  op.create_index('fk_{}_contexts'.format(TABLE_NAME), TABLE_NAME,
                  ['context_id'])
  op.create_index('fk_{}_task'.format(TABLE_NAME), TABLE_NAME,
                  ['task_id'])


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.drop_table(TABLE_NAME)
