# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""
Create missing Admins

Create Date: 2018-06-04 14:00:37.299927
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy import text

from ggrc.migrations import utils
from ggrc.migrations.utils.migrator import get_migration_user_id

revision = 'b1dbfad3bbad'
down_revision = '3a41fc031f53'


def create_doc_temporary_table():
  """Tmp table to store document.id without Admins"""
  sql = """
      CREATE TEMPORARY TABLE documents_wo_admins (
        id int(11) NOT NULL
      )
  """
  op.execute(sql)


def save_documents_no_admins():
  """Store document w/o Admins ids to temp_table documents_wo_admins"""
  sql = """
      INSERT INTO documents_wo_admins (id)
        SELECT d.id FROM documents d
          LEFT OUTER JOIN(
            SELECT DISTINCT(acl.object_id)
              FROM access_control_list acl
              JOIN access_control_roles acr ON acr.id = acl.ac_role_id
                AND acr.name = 'Admin'
                AND acr.object_type = 'Document'
            ) AS res ON res.object_id = d.id
        WHERE res.object_id IS NULL
  """
  op.execute(sql)


def get_document_admin_role_id(connection):
  """Get document admin role id"""
  sql = """
    SELECT id FROM access_control_roles acr
    WHERE acr.name = 'Admin' AND acr.object_type = 'Document'
  """
  return connection.execute(text(sql)).fetchone()[0]


def create_document_missing_admins(connection, migration_user_id,
                                   admin_role_id):
  utils.create_missing_admins(connection, migration_user_id,
                              admin_role_id,
                              object_type="Document",
                              revision_action="created",
                              table_mame="documents_wo_admins")


def add_doc_to_missing_revisions(connection):
  """Add modified Documents to objects_without_revisions to create revisions"""

  utils.add_to_missing_revisions(connection,
                                 table_with_id="documents_wo_admins",
                                 object_type="Document")


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  connection = op.get_bind()
  migration_user_id = get_migration_user_id(connection)
  document_admin_role_id = get_document_admin_role_id(connection)
  create_doc_temporary_table()
  save_documents_no_admins()
  create_document_missing_admins(connection, migration_user_id,
                                 document_admin_role_id)
  add_doc_to_missing_revisions(connection)
  op.execute("DROP TABLE documents_wo_admins")


def downgrade():
  """"Downgrade database schema and/or data back to the previous revision."""
