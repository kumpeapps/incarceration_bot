"""add api_key and amember_user_id to users table

Revision ID: 58546d11f1b5
Revises: 8af7abc98abc
Create Date: 2025-08-11 20:57:39.247822

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
        safe_drop_column,
        migration_summary
    )
except ImportError:
    # Fallback to old migration_utils
    try:
        from migration_utils import (
            column_exists, 
            safe_add_column,
            safe_drop_column,
            migration_summary
        )
    except ImportError as e:
        print(f"Warning: Could not import migration utilities: {e}")
        print("Migration will attempt to run without helper functions")
        
        def column_exists(table_name, column_name):
            """Fallback function - check if column exists"""
            from sqlalchemy import inspect
            try:
                connection = op.get_bind()
                inspector = inspect(connection)
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                return column_name in columns
            except Exception:
                return False
        
        def safe_add_column(table_name, column_name, column_type, **kwargs):
            """Fallback function - add column only if it doesn't exist"""
            if not column_exists(table_name, column_name):
                print(f"Adding column {column_name} to {table_name}")
                op.add_column(table_name, sa.Column(column_name, column_type, **kwargs))
            else:
                print(f"Column {column_name} already exists in {table_name}, skipping")
        
        def safe_drop_column(table_name, column_name):
            """Fallback function - drop column only if it exists"""
            if column_exists(table_name, column_name):
                print(f"Dropping column {column_name} from {table_name}")
                op.drop_column(table_name, column_name)
            else:
                print(f"Column {column_name} doesn't exist in {table_name}, skipping")
        
        def migration_summary(table_name):
            """Fallback function"""
            pass


# revision identifiers, used by Alembic.
revision: str = '58546d11f1b5'
down_revision: Union[str, Sequence[str], None] = '8af7abc98abc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add api_key and amember_user_id columns to users table."""
    print("Adding api_key and amember_user_id columns to users table...")
    
    # Add api_key column (idempotent)
    safe_add_column('users', 'api_key', sa.String(255), nullable=True, unique=True)
    
    # Add amember_user_id column (idempotent)
    safe_add_column('users', 'amember_user_id', sa.Integer(), nullable=True, unique=True)
    
    print("Successfully added api_key and amember_user_id columns")
    migration_summary('users')


def downgrade() -> None:
    """Remove api_key and amember_user_id columns from users table."""
    print("Removing api_key and amember_user_id columns from users table...")
    
    # Remove amember_user_id column (idempotent)
    safe_drop_column('users', 'amember_user_id')
    
    # Remove api_key column (idempotent)
    safe_drop_column('users', 'api_key')
    
    print("Successfully removed api_key and amember_user_id columns")
    migration_summary('users')
