"""add groups and user groups tables

Revision ID: 008_add_groups_and_user_groups
Revises: 47952153bdcf
Create Date: 2025-08-11 16:00:00.000000

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
        safe_create_table,
        safe_drop_table,
        table_exists,
        migration_summary,
        execute_sql_if_condition
    )
except ImportError:
    # Fallback to old migration_utils
    try:
        from migration_utils import (
            column_exists, 
            safe_add_column,
            safe_create_table,
            safe_drop_table,
            table_exists,
            migration_summary,
            execute_sql_if_condition
        )
    except ImportError as e:
        print(f"Warning: Could not import migration utilities: {e}")
        print("Migration will attempt to run without helper functions")
        
        def column_exists(table_name, column_name):
            """Fallback function - always returns False to be safe"""
            return False
        
        def safe_add_column(*args, **kwargs):
            """Fallback function - just calls add_column"""
            op.add_column(*args, **kwargs)
        
        def safe_create_table(table_name, *columns, **kwargs):
            """Fallback function - checks if table exists before creating"""
            from sqlalchemy import inspect
            try:
                connection = op.get_bind()
                inspector = inspect(connection)
                existing_tables = inspector.get_table_names()
                if table_name not in existing_tables:
                    print(f"Creating table {table_name}")
                    op.create_table(table_name, *columns, **kwargs)
                else:
                    print(f"Table {table_name} already exists, skipping creation")
            except Exception as ex:
                print(f"Error checking table existence: {ex}")
                print(f"Attempting to create table {table_name} anyway")
                try:
                    op.create_table(table_name, *columns, **kwargs)
                except Exception as create_ex:
                    if "already exists" in str(create_ex):
                        print(f"Table {table_name} already exists, continuing")
                    else:
                        raise create_ex
        
        def safe_drop_table(table_name):
            """Fallback function - checks if table exists before dropping"""
            from sqlalchemy import inspect
            try:
                connection = op.get_bind()
                inspector = inspect(connection)
                existing_tables = inspector.get_table_names()
                if table_name in existing_tables:
                    print(f"Dropping table {table_name}")
                    op.drop_table(table_name)
                else:
                    print(f"Table {table_name} doesn't exist, skipping")
            except Exception as ex:
                print(f"Error checking table existence: {ex}")
                try:
                    op.drop_table(table_name)
                except Exception as drop_ex:
                    if "doesn't exist" in str(drop_ex) or "Unknown table" in str(drop_ex):
                        print(f"Table {table_name} doesn't exist, continuing")
                    else:
                        raise drop_ex
        
        def table_exists(table_name):
            """Fallback function - check table existence"""
            from sqlalchemy import inspect
            try:
                connection = op.get_bind()
                inspector = inspect(connection)
                return table_name in inspector.get_table_names()
            except Exception:
                return False
        
        def migration_summary(table_name):
            """Fallback function"""
            pass
            
        def execute_sql_if_condition(sql, condition_sql, description="SQL operation"):
            """Fallback function - simplified conditional execution"""
            from sqlalchemy import text
            try:
                connection = op.get_bind()
                # Check the condition
                result = connection.execute(text(condition_sql))
                should_execute = bool(result.fetchone()[0])
                
                if should_execute:
                    print(f"Executing {description}")
                    connection.execute(text(sql))
                else:
                    print(f"Condition not met for {description}, skipping")
            except Exception as e:
                print(f"Warning: Failed to execute {description}: {e}")
                # Try to execute anyway for safety
                try:
                    connection = op.get_bind()
                    connection.execute(text(sql))
                    print(f"Executed {description} without condition check")
                except Exception as e2:
                    print(f"Failed to execute {description}: {e2}")

# revision identifiers, used by Alembic.
revision: str = '008_add_groups_and_user_groups'
down_revision: Union[str, Sequence[str], None] = '47952153bdcf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add groups and user_groups tables, migrate existing role data."""
    print("Adding groups and user_groups tables...")
    
    # Create groups table (idempotent)
    safe_create_table('groups',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='unique_group_name')
    )
    
    # Create user_groups table (idempotent)
    safe_create_table('user_groups',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'group_id', name='unique_user_group')
    )
    
    # Insert default groups (idempotent)
    print("Creating default groups...")
    execute_sql_if_condition(
        sql="""
            INSERT INTO groups (name, display_name, description, is_active)
            VALUES 
            ('admin', 'Administrators', 'Full system access and user management', 1),
            ('user', 'Regular Users', 'Standard user access to monitor functionality', 1),
            ('moderator', 'Moderators', 'Enhanced access for content moderation', 1)
        """,
        condition_sql="SELECT COUNT(*) = 0 FROM groups",
        description="inserting default groups"
    )
    
    # Migrate existing users to groups based on their role (idempotent)
    print("Migrating existing user roles to groups...")
    
    # Check if role column exists
    if column_exists('users', 'role'):
        # Assign admin group to users with admin role (only if not already assigned)
        execute_sql_if_condition(
            sql="""
                INSERT INTO user_groups (user_id, group_id, assigned_by, created_at, updated_at)
                SELECT 
                    u.id,
                    g.id,
                    NULL,
                    NOW(),
                    NOW()
                FROM users u
                CROSS JOIN groups g
                WHERE u.role = 'admin' AND g.name = 'admin'
                AND NOT EXISTS (
                    SELECT 1 FROM user_groups ug2 
                    WHERE ug2.user_id = u.id AND ug2.group_id = g.id
                )
            """,
            condition_sql="""
                SELECT COUNT(*) > 0 
                FROM users u 
                CROSS JOIN groups g 
                WHERE u.role = 'admin' AND g.name = 'admin'
                AND NOT EXISTS (
                    SELECT 1 FROM user_groups ug2 
                    WHERE ug2.user_id = u.id AND ug2.group_id = g.id
                )
            """,
            description="assigning admin users to admin group"
        )
        
        # Assign user group to users with user role or NULL role (only if not already assigned)
        execute_sql_if_condition(
            sql="""
                INSERT INTO user_groups (user_id, group_id, assigned_by, created_at, updated_at)
                SELECT 
                    u.id,
                    g.id,
                    NULL,
                    NOW(),
                    NOW()
                FROM users u
                CROSS JOIN groups g
                WHERE (u.role = 'user' OR u.role IS NULL) AND g.name = 'user'
                AND NOT EXISTS (
                    SELECT 1 FROM user_groups ug2 
                    WHERE ug2.user_id = u.id AND ug2.group_id = g.id
                )
            """,
            condition_sql="""
                SELECT COUNT(*) > 0 
                FROM users u 
                CROSS JOIN groups g 
                WHERE (u.role = 'user' OR u.role IS NULL) AND g.name = 'user'
                AND NOT EXISTS (
                    SELECT 1 FROM user_groups ug2 
                    WHERE ug2.user_id = u.id AND ug2.group_id = g.id
                )
            """,
            description="assigning user/null role users to user group"
        )
    else:
        # If no role column exists, assign all users to user group (only if not already assigned)
        print("No role column found, assigning all users to 'user' group...")
        execute_sql_if_condition(
            sql="""
                INSERT INTO user_groups (user_id, group_id, assigned_by, created_at, updated_at)
                SELECT 
                    u.id,
                    g.id,
                    NULL,
                    NOW(),
                    NOW()
                FROM users u
                CROSS JOIN groups g
                WHERE g.name = 'user'
                AND NOT EXISTS (
                    SELECT 1 FROM user_groups ug2 
                    WHERE ug2.user_id = u.id AND ug2.group_id = g.id
                )
            """,
            condition_sql="""
                SELECT COUNT(*) > 0 
                FROM users u 
                CROSS JOIN groups g 
                WHERE g.name = 'user'
                AND NOT EXISTS (
                    SELECT 1 FROM user_groups ug2 
                    WHERE ug2.user_id = u.id AND ug2.group_id = g.id
                )
            """,
            description="assigning all users to user group"
        )
    
    print("Groups and user_groups tables created successfully")
    migration_summary('groups')
    migration_summary('user_groups')


def downgrade() -> None:
    """Remove groups and user_groups tables, restore role column if needed."""
    print("Removing groups and user_groups tables...")
    
    # If role column doesn't exist, recreate it and populate from groups
    if not column_exists('users', 'role'):
        print("Restoring role column to users table...")
        safe_add_column('users', 'role', sa.String(length=20), nullable=False, server_default='user')
        
        # Update role based on group membership (only if groups table exists)
        if table_exists('user_groups') and table_exists('groups'):
            execute_sql_if_condition(
                sql="""
                    UPDATE users u
                    SET role = 'admin'
                    WHERE u.id IN (
                        SELECT DISTINCT ug.user_id
                        FROM user_groups ug
                        JOIN groups g ON ug.group_id = g.id
                        WHERE g.name = 'admin'
                    )
                """,
                condition_sql="""
                    SELECT COUNT(*) > 0 FROM user_groups ug
                    JOIN groups g ON ug.group_id = g.id
                    WHERE g.name = 'admin'
                """,
                description="restoring admin roles from group membership"
            )
    
    # Drop tables (idempotent)
    safe_drop_table('user_groups')
    safe_drop_table('groups')
    
    if table_exists('users'):
        migration_summary('users')
