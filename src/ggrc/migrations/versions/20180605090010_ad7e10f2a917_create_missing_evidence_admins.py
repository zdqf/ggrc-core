# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
Create missing Evidence Admins

Create Date: 2018-06-05 09:00:10.586460
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from alembic import op
from sqlalchemy import text

from ggrc.migrations import utils
from ggrc.migrations.utils.migrator import get_migration_user_id

# revision identifiers, used by Alembic.
revision = 'ad7e10f2a917'
down_revision = 'b1dbfad3bbad'


def get_evidence_admin_role_id(connection):
  """Get evidence admin role id"""
  sql = """
      SELECT id FROM access_control_roles acr
      WHERE acr.name = 'Admin' AND acr.object_type = 'Evidence'
    """
  return connection.execute(text(sql)).fetchone()[0]


def create_evid_temporary_table():
  """Tmp table to store evidence.id without Admins"""
  sql = """
        CREATE TEMPORARY TABLE evidence_wo_admins (
          id int(11) NOT NULL
        )
    """
  op.execute(sql)


def save_evidence_no_admins():
  """Store evidence w/o Admins ids to temp_table evidence_wo_admins"""
  sql = """
      INSERT INTO evidence_wo_admins (id)
        SELECT e.id FROM evidence e
          LEFT OUTER JOIN(
            SELECT DISTINCT(acl.object_id)
              FROM access_control_list acl
              JOIN access_control_roles acr ON acr.id = acl.ac_role_id
                AND acr.object_type = 'Evidence'
                AND acr.name = 'Admin'
            ) AS res ON res.object_id = e.id
        WHERE res.object_id IS NULL
  """
  op.execute(sql)


def create_evidence_missing_admins(connection, migration_user_id,
                                   evidence_admin_role_id):
  """Insert into access_control_list Evidence admin role

  If we have 'create' revision -> take modified_by_id as Admin
  else set current migration user as evidence Admin
  """
  utils.create_missing_admins(connection, migration_user_id,
                              evidence_admin_role_id,
                              object_type="Evidence",
                              revision_action="created",
                              table_mame="evidence_wo_admins")


def add_evidence_to_missing_revisions(connection):
  """Add modified Evidence to objects_without_revisions to create revisions"""

  utils.add_to_missing_revisions(connection,
                                 table_with_id="evidence_wo_admins",
                                 object_type="Evidence")


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  connection = op.get_bind()
  migration_user_id = get_migration_user_id(connection)
  evidence_admin_role_id = get_evidence_admin_role_id(connection)
  create_evid_temporary_table()
  save_evidence_no_admins()
  create_evidence_missing_admins(connection, migration_user_id,
                                 evidence_admin_role_id)
  add_evidence_to_missing_revisions(connection)
  op.execute("DROP TABLE evidence_wo_admins")


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
