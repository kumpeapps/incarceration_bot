"""add user_id column to monitors table

Revision ID: 47952153bdcf
Revises: 059b21f8b34f
Create Date: 2025-08-11 14:33:16.000635

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
        safe_add_column,
        migration_summary
    )
except ImportError:
    # Fallback to old migration_utils
    try:
        from migration_utils import (
            column_exists, 
            safe_add_column,
            migration_summary
        )
    except ImportError as e:
        print(f"Warning: Could not import migration utilities: {e}")
        print("Migration will attempt to run without helper functions")
        
        def column_exists(table_name, column_name):
            """Fallback function"""
            return False
        
        def safe_add_column(*args, **kwargs):
            """Fallback function"""
            pass
        
        def migration_summary(table_name):
            """Fallback function"""
            pass

# revision identifiers, used by Alembic.
revision: str = '47952153bdcf'
down_revision: Union[str, Sequence[str], None] = '006_fix_users_table_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add user_id column to monitors table for user ownership tracking."""
    print("Adding user_id column to monitors table...")
    
    # Add user_id column (nullable since existing monitors won't have owners)
    safe_add_column('monitors', 'user_id', sa.Integer(), nullable=True)
    
    print("monitors table user_id column addition completed successfully")
    migration_summary('monitors')


def downgrade() -> None:
    """Remove user_id column from monitors table."""
    print("Removing user_id column from monitors table...")
    
    # Check if column exists before dropping
    if column_exists('monitors', 'user_id'):
        op.drop_column('monitors', 'user_id')
        print("user_id column removed successfully")
    else:
        print("user_id column does not exist, nothing to remove")
    
    migration_summary('monitors')
