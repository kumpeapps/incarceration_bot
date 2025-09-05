"""Add password_format column to users table

Revision ID: 007_add_password_format
Revises: 006_fix_users_table_columns
Create Date: 2025-08-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from migration_utils import safe_add_column, safe_drop_column

# revision identifiers, used by Alembic.
revision = '007_add_password_format'
down_revision = '006_fix_users_table_columns'
branch_labels = None
depends_on = None


def upgrade():
    """Add password_format column to users table."""
    # Add password_format column with default value
    safe_add_column('users', 'password_format', sa.String(length=20), nullable=False, default='bcrypt')


def downgrade():
    """Remove password_format column from users table."""
    safe_drop_column('users', 'password_format')
