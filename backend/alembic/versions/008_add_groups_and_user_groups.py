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
        migration_summary,
        execute_sql_if_condition
    )
except ImportError:
    # Fallback to old migration_utils
    try:
        from migration_utils import (
            column_exists, 
            safe_add_column,
            migration_summary,
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
        
        def migration_summary(table_name):
            """Fallback function"""
            pass
            
        def execute_sql_if_condition(sql, condition_sql, description="SQL operation"):
            """Fallback function"""
            pass

# revision identifiers, used by Alembic.
revision: str = '008_add_groups_and_user_groups'
down_revision: Union[str, Sequence[str], None] = '47952153bdcf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add groups and user_groups tables, migrate existing role data."""
    print("Adding groups and user_groups tables...")
    
    # Create groups table
    op.create_table('groups',
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
    
    # Create user_groups table
    op.create_table('user_groups',
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
    
    # Insert default groups
    print("Creating default groups...")
    op.execute("""
        INSERT INTO groups (name, display_name, description, is_active)
        VALUES 
        ('admin', 'Administrators', 'Full system access and user management', 1),
        ('user', 'Regular Users', 'Standard user access to monitor functionality', 1),
        ('moderator', 'Moderators', 'Enhanced access for content moderation', 1)
    """)
    
    # Migrate existing users to groups based on their role
    print("Migrating existing user roles to groups...")
    
    # Check if role column exists
    if column_exists('users', 'role'):
        # Assign admin group to users with admin role
        op.execute("""
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
        """)
        
        # Assign user group to users with user role or NULL role
        op.execute("""
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
        """)
    else:
        # If no role column exists, assign all users to user group
        print("No role column found, assigning all users to 'user' group...")
        op.execute("""
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
        """)
    
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
        
        # Update role based on group membership
        op.execute("""
            UPDATE users u
            SET role = 'admin'
            WHERE u.id IN (
                SELECT DISTINCT ug.user_id
                FROM user_groups ug
                JOIN groups g ON ug.group_id = g.id
                WHERE g.name = 'admin'
            )
        """)
    
    # Drop tables
    op.drop_table('user_groups')
    op.drop_table('groups')
    
    migration_summary('users')
