"""add monitor inmate links table

Revision ID: 005_monitor_inmate_links
Revises: b47722ea223c
Create Date: 2025-08-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import os
import sys

# Add the alembic directory to the path to import migration_utils
alembic_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(alembic_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    # Try new package structure first
    from alembic.utils import (
        table_exists, 
        safe_create_table,
        safe_drop_table,
        migration_summary
    )
except ImportError:
    # Fallback to old migration_utils
    try:
        from migration_utils import (
            table_exists, 
            safe_create_table,
            safe_drop_table,
            migration_summary
        )
    except ImportError as e:
        print(f"Warning: Could not import migration utilities: {e}")
        print("Migration will attempt to run without helper functions")
        
        def table_exists(table_name):
            """Fallback function"""
            return False
        
        def safe_create_table(*args, **kwargs):
            """Fallback function"""
            try:
                op.create_table(*args, **kwargs)
            except Exception as e:
                print(f"Warning: Could not create table: {e}")
        
        def safe_drop_table(table_name):
            """Fallback function"""
            try:
                op.drop_table(table_name)
            except Exception as e:
                print(f"Warning: Could not drop table {table_name}: {e}")
        
        def migration_summary(table_name):
            """Fallback function"""
            pass

# revision identifiers, used by Alembic.
revision = '005_monitor_inmate_links'
down_revision = 'b47722ea223c'
branch_labels = None
depends_on = None


def upgrade():
    """Add monitor inmate links and users tables."""
    print("Creating users and monitor_inmate_links tables...")
    
    # First, create users table if it doesn't exist
    if not table_exists('users'):
        safe_create_table('users',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('username', sa.String(length=50), nullable=False),
            sa.Column('email', sa.String(length=100), nullable=False),
            sa.Column('password_hash', sa.String(length=255), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('username'),
            sa.UniqueConstraint('email')
        )
        print("users table created successfully")
    else:
        print("users table already exists, skipping creation")
    
    # Create monitor_inmate_links table if it doesn't exist
    if not table_exists('monitor_inmate_links'):
        safe_create_table('monitor_inmate_links',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('monitor_id', sa.Integer(), nullable=False),
            sa.Column('inmate_id', sa.Integer(), nullable=False),
            sa.Column('linked_by_user_id', sa.Integer(), nullable=False),
            sa.Column('is_excluded', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('link_reason', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['inmate_id'], ['inmates.idinmates'], ),
            sa.ForeignKeyConstraint(['linked_by_user_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['monitor_id'], ['monitors.idmonitors'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('monitor_id', 'inmate_id', name='unique_monitor_inmate_link')
        )
        print("monitor_inmate_links table created successfully")
    else:
        print("monitor_inmate_links table already exists, skipping creation")
    
    print("Users and monitor inmate links table creation completed successfully")
    migration_summary('users')
    migration_summary('monitor_inmate_links')


def downgrade():
    """Remove monitor inmate links and users tables."""
    print("Removing monitor_inmate_links and users tables...")
    
    # Drop tables in reverse order (due to foreign key constraints)
    if table_exists('monitor_inmate_links'):
        safe_drop_table('monitor_inmate_links')
        print("monitor_inmate_links table removed successfully")
    else:
        print("monitor_inmate_links table does not exist, nothing to remove")
    
    if table_exists('users'):
        safe_drop_table('users')
        print("users table removed successfully")
    else:
        print("users table does not exist, nothing to remove")
    
    migration_summary('users')
    migration_summary('monitor_inmate_links')
