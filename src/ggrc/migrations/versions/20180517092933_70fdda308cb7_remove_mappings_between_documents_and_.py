# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Remove mappings between Documents and Comments

Create Date: 2018-05-17 09:29:33.265515
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from alembic import op

# revision identifiers, used by Alembic.
revision = '70fdda308cb7'
down_revision = '776825e9f919'


def upgrade():
    """Upgrade database schema and/or data, creating a new revision."""
    op.execute('SET SESSION SQL_SAFE_UPDATES = 0')

    sql = """
        DELETE FROM relationships  
        WHERE id IN (
            SELECT s.id FROM (
                SELECT r.id FROM relationships r WHERE 
                    r.source_type="Document" AND r.destination_type="Comment"
                UNION ALL
                SELECT r.id FROM relationships r WHERE 
                    r.destination_type="Document" AND r.source_type="Comment"
            ) AS s
        )
    """
    op.execute(sql)



def downgrade():
    """Downgrade database schema and/or data back to the previous revision."""
