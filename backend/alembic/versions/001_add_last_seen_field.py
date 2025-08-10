"""Add last_seen field to inmates table

Revision ID: 001
Revises: 
Create Date: 2025-08-09 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add last_seen column
    op.add_column('inmates', sa.Column('last_seen', sa.DateTime, nullable=True))
    
    # Update existing records: set last_seen to in_custody_date for active inmates
    # Using database-agnostic SQLAlchemy operations
    connection = op.get_bind()
    
    # For active inmates (no release date), set last_seen to in_custody_date
    connection.execute(text('''
        UPDATE inmates 
        SET last_seen = in_custody_date 
        WHERE last_seen IS NULL 
        AND (release_date = '' OR release_date IS NULL)
    '''))

def downgrade():
    op.drop_column('inmates', 'last_seen')
