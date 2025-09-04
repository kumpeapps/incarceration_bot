"""Add sessions table for login tracking

Revision ID: add_sessions_table
Revises: 
Create Date: 2025-08-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import migration utilities
from migration_utils import table_exists

# revision identifiers
revision = 'add_sessions_table'
down_revision = None
depends_on = None


def upgrade():
    """Add sessions table for tracking user login activity."""
    # Create sessions table only if it doesn't exist
    if not table_exists('sessions'):
        print("Creating sessions table")
        op.create_table('sessions',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('session_token', sa.String(length=255), nullable=False),
            sa.Column('login_time', sa.DateTime(), nullable=False),
            sa.Column('logout_time', sa.DateTime(), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('session_token')
        )
        
        # Create indexes for performance
        op.create_index('idx_sessions_user_id', 'sessions', ['user_id'])
        op.create_index('idx_sessions_is_active', 'sessions', ['is_active'])
    else:
        print("Sessions table already exists, skipping creation")
    op.create_index('idx_sessions_login_time', 'sessions', ['login_time'])


def downgrade():
    """Remove sessions table."""
    if table_exists('sessions'):
        print("Removing sessions table and indexes")
        try:
            op.drop_index('idx_sessions_login_time', table_name='sessions')
        except Exception as e:
            print(f"Warning: Could not drop idx_sessions_login_time: {e}")
        
        try:
            op.drop_index('idx_sessions_is_active', table_name='sessions')
        except Exception as e:
            print(f"Warning: Could not drop idx_sessions_is_active: {e}")
        
        try:
            op.drop_index('idx_sessions_user_id', table_name='sessions')
        except Exception as e:
            print(f"Warning: Could not drop idx_sessions_user_id: {e}")
        
        op.drop_table('sessions')
        print("Sessions table removed successfully")
    else:
        print("Sessions table does not exist, nothing to remove")
