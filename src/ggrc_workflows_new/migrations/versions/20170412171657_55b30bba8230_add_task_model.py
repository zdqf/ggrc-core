# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
Add table for Task model.

Create Date: 2017-04-05 13:23:22.022321
"""
# Skip all pylint checks because this migration has duplicate lines with
# another one.
# pylint: skip-file
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '55b30bba8230'
down_revision = '4be9d0c0242a'
TABLE_NAME = 'tasks'


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  NOT_STARTED_STATUS = u'Not Started'
  IN_PROGRESS_STATUS = u'In Progress'
  FINISHED_STATUS = u'Finished'
  TEMPLATE_STATUS = u'Template'
  VALID_STATUSES = (NOT_STARTED_STATUS, IN_PROGRESS_STATUS, FINISHED_STATUS,
                    TEMPLATE_STATUS)
  op.create_table(
      TABLE_NAME,
      sa.Column('description', sa.Text()),
      sa.Column('title', sa.String(length=250), nullable=False),
      sa.Column('slug', sa.String(length=250), nullable=False),
      sa.Column('modified_by_id', sa.Integer()),
      sa.Column('created_at', sa.DateTime(), nullable=False),
      sa.Column('updated_at', sa.DateTime(), nullable=False),
      sa.Column('context_id', sa.Integer()),
      sa.Column('id', sa.Integer(), primary_key=True),
      sa.Column('contact_id', sa.Integer(), nullable=False),
      sa.Column('status', sa.Enum(*VALID_STATUSES), nullable=False),
      sa.Column('start_date', sa.Date(), nullable=False),
      sa.Column('end_date', sa.Date(), nullable=False),
      # sa.Column('workflow_id', sa.Integer(), nullable=False),
      sa.Column('parent_id', sa.Integer()),
      sa.ForeignKeyConstraint(['context_id'], ['contexts.id'],
                              'fk_task_context_id'),
      sa.ForeignKeyConstraint(['contact_id'], ['people.id'],
                              'fk_task_people_id'),
      # sa.ForeignKeyConstraint(['workflow_id'], ['workflows_new.id'],
      #                         'fk_task_workflow_new_id', ondelete='CASCADE'),
      sa.ForeignKeyConstraint(['parent_id'], ['{}.id'.format(TABLE_NAME)],
                              'fk_task_task_id', ondelete='CASCADE'),
  )
  op.create_unique_constraint('uq_{}'.format(TABLE_NAME), TABLE_NAME, ["slug"])
  op.create_index('ix_{}_created_at'.format(TABLE_NAME), TABLE_NAME,
                  ['created_at'])
  op.create_index('ix_{}_updated_at'.format(TABLE_NAME), TABLE_NAME,
                  ['updated_at'])
  op.create_index('fk_{}_contexts'.format(TABLE_NAME), TABLE_NAME,
                  ['context_id'])
  op.create_index('fk_{}_contact'.format(TABLE_NAME), TABLE_NAME,
                  ['contact_id'])
  # op.create_index('fk_{}_workflow'.format(TABLE_NAME), TABLE_NAME,
  #                 ['workflow_id'])
  op.create_index('fk_{}_parent_id'.format(TABLE_NAME), TABLE_NAME,
                  ['parent_id'])


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.drop_table(TABLE_NAME)
