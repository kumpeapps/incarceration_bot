"""Add index on inmates.last_seen for optimization

Revision ID: 009_optimize_last_seen
Revises: 008_add_groups_and_user_groups
Create Date: 2025-08-14 20:00:00.000000

This migration adds an index on the last_seen column to improve performance
of conditional timestamp updates used to reduce binlog bloat.
"""
from alembic import op
import sqlalchemy as sa
from alembic.operations import ops
from alembic.runtime.environment import EnvironmentContext
from sqlalchemy import text
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import migration utilities
from migration_utils import safe_add_index, safe_execute

# revision identifiers, used by Alembic.
revision = '009_optimize_last_seen'
down_revision = '008_add_groups_and_user_groups'
branch_labels = None
depends_on = None


def upgrade():
    """Add optimization index for last_seen column."""
    
    # Add index on last_seen column for better performance of conditional updates
    safe_add_index(
        'inmates',
        'idx_inmates_last_seen',
        ['last_seen'],
        if_not_exists=True
    )
    
    # Add compound index for jail_id + last_seen for common queries
    safe_add_index(
        'inmates', 
        'idx_inmates_jail_last_seen',
        ['jail_id', 'last_seen'],
        if_not_exists=True
    )
    
    # Add index on monitors.last_seen_incarcerated for release checking
    safe_add_index(
        'monitors',
        'idx_monitors_last_seen_incarcerated', 
        ['last_seen_incarcerated'],
        if_not_exists=True
    )
    
    # Add compound index for jail + last_seen_incarcerated + release_date
    safe_add_index(
        'monitors',
        'idx_monitors_jail_last_seen_release',
        ['jail', 'last_seen_incarcerated', 'release_date'],
        if_not_exists=True
    )


def downgrade():
    """Remove optimization indexes."""
    
    # Remove indexes in reverse order
    safe_execute("DROP INDEX IF EXISTS idx_monitors_jail_last_seen_release ON monitors")
    safe_execute("DROP INDEX IF EXISTS idx_monitors_last_seen_incarcerated ON monitors") 
    safe_execute("DROP INDEX IF EXISTS idx_inmates_jail_last_seen ON inmates")
    safe_execute("DROP INDEX IF EXISTS idx_inmates_last_seen ON inmates")
