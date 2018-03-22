# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Add In Progress status to import_export job

Create Date: 2018-03-22 13:38:39.016030
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision = '9b75e604c326'
down_revision = 'd1671a8dac7'


IMPORT_EXPORT_STATUSES_OLD = ['Not Started', 'Analysis', 'Blocked',
                              'Analysis Failed', 'Stopped', 'Failed',
                              'Finished']

IMPORT_EXPORT_STATUSES_NEW = ['Not Started', 'Analysis', 'Blocked',
                              'Analysis Failed', 'Stopped', 'Failed',
                              'Finished', 'In Progress']


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  op.alter_column(
      'import_exports', 'status',
      type_=sa.Enum(*IMPORT_EXPORT_STATUSES_NEW),
      existing_type=sa.Enum(*IMPORT_EXPORT_STATUSES_OLD),
      nullable=False,
      default='Not Started')


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
