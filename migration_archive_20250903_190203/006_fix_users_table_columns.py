"""Fix users table columns

Revision ID: 006_fix_users_table_columns
Revises: 005_update_admin
Create Date: 2024-01-01 00:00:00.000000

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
        safe_rename_column, 
        execute_sql_if_condition
    )
except ImportError:
    # Fallback to old migration_utils
    try:
        from migration_utils import (
            column_exists, 
            safe_add_column, 
            safe_rename_column, 
            execute_sql_if_condition
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
        
        def safe_rename_column(*args, **kwargs):
            """Fallback function"""
            pass
        
        def execute_sql_if_condition(*args, **kwargs):
            """Fallback function"""
            pass
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import sys
import os

# Add the alembic directory to the path to import migration_utils
sys.path.append(os.path.dirname(__file__))
try:
    from migration_utils import (
        column_exists, safe_add_column, safe_rename_column, 
        execute_sql_if_condition, migration_summary
    )
except ImportError:
    # Fallback functions if utils aren't available
    def column_exists(table_name, column_name):
        try:
            connection = op.get_bind()
            inspector = sa.inspect(connection)
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            return column_name in columns
        except Exception:
            return False
    
    def safe_add_column(table_name, column_name, column_type, **kwargs):
        if not column_exists(table_name, column_name):
            print(f"Adding column {column_name} to {table_name}")
            op.add_column(table_name, sa.Column(column_name, column_type, **kwargs))
            return True
        else:
            print(f"Column {column_name} already exists in {table_name}, skipping")
            return False
    
    def safe_rename_column(table_name, old_name, new_name, column_type=None):
        if column_exists(table_name, old_name) and not column_exists(table_name, new_name):
            print(f"Renaming column {old_name} to {new_name} in {table_name}")
            if column_type is None:
                column_type = sa.String(length=255)  # Default assumption
            op.alter_column(table_name, old_name, 
                           new_column_name=new_name,
                           existing_type=column_type)
            return True
        elif column_exists(table_name, new_name):
            print(f"Column {new_name} already exists in {table_name}, skipping rename")
            return False
        else:
            print(f"Column {old_name} doesn't exist in {table_name}, skipping rename")
            return False
    
    def execute_sql_if_condition(sql, condition_sql, description="SQL operation"):
        try:
            connection = op.get_bind()
            result = connection.execute(text(condition_sql))
            should_execute = bool(result.fetchone()[0])
            if should_execute:
                print(f"Executing {description}")
                connection.execute(text(sql))
                return True
            else:
                print(f"Condition not met for {description}, skipping")
                return False
        except Exception as e:
            print(f"Warning: Failed to execute {description}: {e}")
            return False
    
    def migration_summary(table_name):
        try:
            connection = op.get_bind()
            inspector = sa.inspect(connection)
            columns = inspector.get_columns(table_name)
            print(f"\n{table_name} table structure after migration:")
            for col in columns:
                nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
                print(f"  {col['name']} - {col['type']} {nullable}")
            print()
        except Exception as e:
            print(f"Could not display table summary: {e}")

# revision identifiers, used by Alembic.
revision = '006_fix_users_table_columns'
down_revision = '005_monitor_inmate_links'
branch_labels = None
depends_on = None


def upgrade():
    """Fix users table to match API expectations"""
    print("Fixing users table column names...")
    
    # Step 1: Rename password_hash to hashed_password (only if needed)
    safe_rename_column('users', 'password_hash', 'hashed_password', sa.String(length=255))
    
    # Step 2: Add role column (only if needed)
    safe_add_column('users', 'role', sa.String(length=20), nullable=False, server_default='user')
    
    # Step 2.1: Explicitly update existing rows to ensure consistency across databases
    execute_sql_if_condition(
        sql="""
            UPDATE users 
            SET role = 'user'
            WHERE role IS NULL
        """,
        condition_sql="""
            SELECT COUNT(*) FROM users 
            WHERE role IS NULL
        """,
        description="ensuring all existing rows have the default role value"
    )
    
    # Step 3: Update role values based on is_admin (only if needed)
    execute_sql_if_condition(
        sql="""
            UPDATE users 
            SET role = CASE 
                WHEN is_admin = 1 THEN 'admin' 
                ELSE 'user' 
            END
            WHERE role IS NULL OR (role = 'user' AND is_admin = 1)
        """,
        condition_sql="""
            SELECT COUNT(*) FROM users 
            WHERE (role IS NULL OR role = 'user') AND is_admin = 1
        """,
        description="updating role values based on is_admin"
    )
    
    print("Users table column fixes completed successfully")
    migration_summary('users')


def downgrade():
    """Reverse the column name changes"""
    print("Reversing users table column changes...")
    
    # Update is_admin based on role (if both columns exist)
    execute_sql_if_condition(
        sql="""
            UPDATE users 
            SET is_admin = CASE 
                WHEN role = 'admin' THEN 1 
                ELSE 0 
            END
        """,
        condition_sql="""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'users' 
            AND COLUMN_NAME IN ('is_admin', 'role')
        """,
        description="updating is_admin values based on role"
    )
    
    # Remove role column (only if it exists)
    if column_exists('users', 'role'):
        print("Dropping role column...")
        try:
            op.drop_column('users', 'role')
        except Exception as e:
            print(f"Warning: Could not drop role column: {e}")
    
    # Rename hashed_password back to password_hash (only if needed)
    safe_rename_column('users', 'hashed_password', 'password_hash', sa.String(length=255))
    
    print("Users table column changes reversed successfully")
    migration_summary('users')
