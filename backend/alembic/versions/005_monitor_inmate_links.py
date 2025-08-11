"""add monitor inmate links table

Revision ID: 005_monitor_inmate_links
Revises: b47722ea223c
Create Date: 2025-08-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_monitor_inmate_links'
down_revision = 'b47722ea223c'
branch_labels = None
depends_on = None


def upgrade():
    # First, create users table if it doesn't exist
    op.create_table('users',
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
    
    # Create monitor_inmate_links table
    op.create_table('monitor_inmate_links',
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


def downgrade():
    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_table('monitor_inmate_links')
    op.drop_table('users')
