# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
Update send by default evidence field

Create Date: 2018-06-04 10:00:18.433654
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.

revision = '3a41fc031f53'
down_revision = 'f77f9a8aff84'


def update_send_by_default():
  """Update missing values to True"""
  op.execute("SET SESSION SQL_SAFE_UPDATES = 0")
  sql = """
      UPDATE evidence e SET e.send_by_default=1 WHERE e.send_by_default IS NULL
  """
  op.execute(sql)


def alter_evidence():
  """Make send_by_default column not nullable and True by default"""
  op.alter_column(
      "evidence",
      "send_by_default",
      nullable=False,
      server_default=sa.true(),
      existing_type=sa.Boolean(),
      existing_nullable=True,
      existing_server_default=None,
  )


def add_evidence_recipients():
  """Add evidence admin to comment notification recipient list"""
  op.execute("SET SESSION SQL_SAFE_UPDATES = 0")
  sql = """
      UPDATE evidence e SET e.recipients="Admin" WHERE e.recipients IS NULL
  """
  op.execute(sql)


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  update_send_by_default()
  alter_evidence()
  add_evidence_recipients()


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.alter_column(
      "evidence",
      "send_by_default",
      nullable=True,
      server_default=None,
      existing_type=sa.Boolean(),
      existing_nullable=False,
      existing_server_default=sa.true()
  )
