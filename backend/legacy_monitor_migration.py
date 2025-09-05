#!/usr/bin/env python3
"""
Legacy Migration Script for Monitor Table
This is now integrated into the comprehensive schema_migrator.py
Kept for backwards compatibility and standalone usage
"""

import sys
import os
import logging

# Add paths for different environments
sys.path.append('/app')          # For container environments  
sys.path.append('.')             # For local environments
sys.path.append('./backend')     # For running from project root
sys.path.append('../backend')    # For running from subdirectories

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from database_connect import new_session
except ImportError:
    # Try backend subdirectory
    sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
    from database_connect import new_session

from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError, ProgrammingError

def check_column_exists(session, table_name, column_name):
    """Check if a column exists in a table."""
    try:
        inspector = inspect(session.bind)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception:
        # Fallback method for databases that don't support inspection
        try:
            session.execute(text(f"SELECT {column_name} FROM {table_name} LIMIT 0"))
            return True
        except (OperationalError, ProgrammingError):
            return False

def get_database_type(session):
    """Detect database type."""
    dialect_name = session.bind.dialect.name.lower()
    if 'mysql' in dialect_name or 'mariadb' in dialect_name:
        return 'mysql'
    elif 'postgres' in dialect_name:
        return 'postgresql'
    elif 'sqlite' in dialect_name:
        return 'sqlite'
    else:
        return 'unknown'

def migrate_monitors_table():
    """Migrate monitors table to include all required columns."""
    logger.info("🚀 Starting Monitor table migration...")
    
    session = new_session()
    try:
        # Check if monitors table exists
        if not check_column_exists(session, 'monitors', 'id'):
            logger.error("❌ Monitors table does not exist!")
            return False
        
        db_type = get_database_type(session)
        logger.info(f"🔍 Detected database type: {db_type}")
        
        # Define columns that should exist in monitors table
        required_columns = {
            'name': 'VARCHAR(255) NOT NULL',
            'arrest_date': 'DATE',
            'arrest_reason': 'TEXT',
            'booking_number': 'VARCHAR(100)',
            'bail_amount': 'VARCHAR(100)',
            'court_date': 'DATE',
            'cell_location': 'VARCHAR(100)',
            'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP' if db_type == 'mysql' else 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'updated_at': 'DATETIME ON UPDATE CURRENT_TIMESTAMP' if db_type == 'mysql' else 'TIMESTAMP'
        }
        
        columns_added = 0
        
        for column_name, column_definition in required_columns.items():
            if not check_column_exists(session, 'monitors', column_name):
                logger.info(f"  📝 Adding missing column: {column_name}")
                
                try:
                    sql = f"ALTER TABLE monitors ADD COLUMN {column_name} {column_definition}"
                    session.execute(text(sql))
                    session.commit()
                    logger.info(f"  ✅ Added {column_name} successfully")
                    columns_added += 1
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if 'duplicate' in error_msg or 'already exists' in error_msg:
                        logger.info(f"  ℹ️  {column_name} already exists")
                    else:
                        logger.error(f"  ❌ Error adding {column_name}: {e}")
                        session.rollback()
                        return False
            else:
                logger.info(f"  ✅ Column {column_name} already exists")
        
        if columns_added > 0:
            logger.info(f"🎉 Migration completed! Added {columns_added} columns to monitors table")
        else:
            logger.info("✅ All required columns already exist in monitors table")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def verify_migration():
    """Verify that the migration was successful."""
    logger.info("🔍 Verifying migration...")
    
    session = new_session()
    try:
        # Test the query that was failing
        result = session.execute(text("SELECT name, arrest_date FROM monitors LIMIT 1"))
        logger.info("✅ Migration verification passed - monitors.arrest_date column accessible")
        return True
    except Exception as e:
        logger.error(f"❌ Migration verification failed: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    """Direct execution for standalone usage."""
    print("⚠️  WARNING: This script is now deprecated!")
    print("💡 The comprehensive schema_migrator.py should be used instead")
    print("📍 This script is kept for backwards compatibility only")
    print("=" * 60)
    
    if migrate_monitors_table():
        if verify_migration():
            print("🎉 Migration and verification completed successfully!")
        else:
            print("⚠️  Migration completed but verification failed")
    else:
        print("❌ Migration failed!")
    
    print("=" * 60)
    print("💡 For future use, please use: python backend/schema_migrator.py")
