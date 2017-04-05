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
      sa.Column('description', sa.Text())
  )


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.drop_table(table_name)
