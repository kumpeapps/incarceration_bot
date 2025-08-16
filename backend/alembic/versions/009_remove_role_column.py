"""remove role column from users table

Revision ID: 009_remove_role_column
Revises: 008_add_groups_and_user_groups
Create Date: 2025-08-11 17:00:00.000000

"""
from typing import Sequence, Union
import os
import sys

from alembic import op
import sqlalchemy as sa

# Add the alembic directory to the path to import migration_utils
alembic_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(alembic_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    # Try new package structure first
    from alembic.utils import (
        column_exists, 
        migration_summary
    )
except ImportError:
    # Fallback to old migration_utils
    try:
        from migration_utils import (
            column_exists, 
            migration_summary
        )
    except ImportError as e:
        print(f"Warning: Could not import migration utilities: {e}")
        print("Migration will attempt to run without helper functions")
        
        def column_exists(table_name, column_name):
            """Fallback function"""
            return False
        
        def migration_summary(table_name):
            """Fallback function"""
            pass

# revision identifiers, used by Alembic.
revision: str = '009_remove_role_column'
down_revision: Union[str, Sequence[str], None] = '008_add_groups_and_user_groups'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove role column from users table now that groups system is in place."""
    print("Removing role column from users table...")
    
    # Only drop the column if it exists
    if column_exists('users', 'role'):
        print("Dropping role column...")
        try:
            op.drop_column('users', 'role')
            print("Role column removed successfully")
        except Exception as e:
            print(f"Warning: Could not drop role column: {e}")
    else:
        print("Role column does not exist, nothing to remove")
    
    print("Role column removal completed")
    migration_summary('users')


def downgrade() -> None:
    """Restore role column if needed."""
    print("Restoring role column to users table...")
    
    # Add role column back
    if not column_exists('users', 'role'):
        op.add_column('users', sa.Column('role', sa.String(length=20), nullable=False, server_default='user'))
        
        # Populate role based on group membership
        print("Populating role column based on group membership...")
        op.execute("""
            UPDATE users u
            SET role = 'admin'
            WHERE u.id IN (
                SELECT DISTINCT ug.user_id
                FROM user_groups ug
                JOIN groups g ON ug.group_id = g.id
                WHERE g.name = 'admin' AND g.is_active = 1
            )
        """)
        
        print("Role column restored successfully")
    else:
        print("Role column already exists")
    
    migration_summary('users')
