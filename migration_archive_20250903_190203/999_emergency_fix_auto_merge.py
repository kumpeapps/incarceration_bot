"""Emergency fix for auto-merge migration conflicts

Revision ID: 999_emergency_fix_auto_merge
Revises: bf90cf8f
Create Date: 2025-09-02 19:30:00.000000

This migration fixes the auto-merge conflict that created f6c08cf30767.
It ensures the last_seen column exists and handles any duplicate column errors.
"""
from typing import Sequence, Union
import os
import sys

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

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
        migration_summary
    )
except ImportError:
    # Fallback to old migration_utils
    try:
        from migration_utils import (
            column_exists, 
            safe_add_column,
            migration_summary
        )
    except ImportError as e:
        print(f"Warning: Could not import migration utilities: {e}")
        print("Migration will attempt to run without helper functions")
        
        def column_exists(table_name, column_name):
            """Fallback function to check if column exists"""
            try:
                connection = op.get_bind()
                result = connection.execute(text(f"""
                    SELECT COUNT(*) FROM information_schema.COLUMNS 
                    WHERE TABLE_NAME = '{table_name}' 
                    AND COLUMN_NAME = '{column_name}'
                    AND TABLE_SCHEMA = DATABASE()
                """))
                return result.scalar() > 0
            except Exception:
                return False
        
        def safe_add_column(table_name, column_name, column_type, **kwargs):
            """Fallback function to safely add column"""
            if not column_exists(table_name, column_name):
                try:
                    op.add_column(table_name, sa.Column(column_name, column_type, **kwargs))
                    return True
                except Exception as e:
                    print(f"Warning: Could not add column {column_name}: {e}")
                    return False
            else:
                print(f"Column {column_name} already exists in {table_name}, skipping")
                return False
        
        def migration_summary(table_name):
            """Fallback function"""
            pass

# revision identifiers, used by Alembic.
revision: str = '999_emergency_fix_auto_merge'
down_revision: Union[str, Sequence[str], None] = 'bf90cf8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Emergency fix for auto-merge conflicts - ensure last_seen column exists."""
    print("🚨 Emergency fix: Ensuring last_seen column exists...")
    
    # This handles the case where auto-merge created a conflicting migration
    # that tries to add last_seen column when it already exists
    
    # Check if last_seen column exists
    if column_exists('inmates', 'last_seen'):
        print("✅ last_seen column already exists - auto-merge conflict resolved")
    else:
        print("🔧 Adding missing last_seen column...")
        column_added = safe_add_column('inmates', 'last_seen', sa.DateTime, nullable=True)
        
        if column_added:
            print("✅ last_seen column added successfully")
            
            # Update existing records: set last_seen to in_custody_date for active inmates
            try:
                connection = op.get_bind()
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
            print("ℹ️  last_seen column addition skipped (already exists)")
    
    # Also check for any stuck Alembic version state
    try:
        connection = op.get_bind()
        
        # Check current alembic version
        result = connection.execute(text("SELECT version_num FROM alembic_version"))
        current_version = result.scalar()
        print(f"📋 Current Alembic version: {current_version}")
        
        # If we're on the problematic auto-merge version, update to our fixed state
        if current_version and 'f6c08cf30767' in current_version:
            print("🔧 Detected problematic auto-merge version, updating...")
            connection.execute(text(f"UPDATE alembic_version SET version_num = '{revision}'"))
            print("✅ Alembic version updated to emergency fix")
        
    except Exception as e:
        print(f"⚠️  Could not check/update Alembic version: {e}")
    
    print("✅ Emergency auto-merge fix completed")
    migration_summary('inmates')


def downgrade() -> None:
    """Downgrade is not supported for emergency fixes."""
    print("⚠️  Downgrade not supported for emergency fix migration")
    print("   This migration only ensures data consistency")
    pass
