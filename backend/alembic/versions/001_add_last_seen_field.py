"""Add last_seen field to inmates table

Revision ID: 001
Revises: 
Create Date: 2025-08-09 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import sys
import os

# Add the migration_utils to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
from migration_utils import safe_add_column

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    print("📝 Adding last_seen field to inmates table...")
    
    # Add last_seen column safely
    column_added = safe_add_column('inmates', 'last_seen', sa.DateTime, nullable=True)
    
    if column_added:
        print("✅ Added last_seen column")
        
        # Update existing records: set last_seen to in_custody_date for active inmates
        connection = op.get_bind()
        
        try:
            # For active inmates (no release date), set last_seen to in_custody_date
            result = connection.execute(text('''
                UPDATE inmates 
                SET last_seen = in_custody_date 
                WHERE last_seen IS NULL 
                AND (release_date = '' OR release_date IS NULL)
            '''))
            
            updated_rows = result.rowcount if hasattr(result, 'rowcount') else 0
            print(f"✅ Updated {updated_rows} existing records with last_seen values")
            
        except Exception as e:
            print(f"⚠️  Could not update existing records: {e}")
    else:
        print("ℹ️  last_seen column already exists, no changes needed")

def downgrade():
    from migration_utils import safe_drop_column
    print("🔄 Removing last_seen field from inmates table...")
    dropped = safe_drop_column('inmates', 'last_seen')
    if dropped:
        print("✅ Removed last_seen column")
    else:
        print("ℹ️  last_seen column doesn't exist, no changes needed")
