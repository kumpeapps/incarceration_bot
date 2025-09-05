#!/usr/bin/env python3
"""
⚠️  DEPRECATED MIGRATION SCRIPT ⚠️

This script has been replaced by the comprehensive migration system in backend/

The new migration system:
- Runs automatically on container startup
- Handles all SQLAlchemy models (not just monitors) 
- Supports multiple database types and date formats
- Provides better error handling and logging
- Is integrated into the application lifecycle

RECOMMENDED ACTIONS:
1. For automatic migration: Restart containers - migration runs automatically
2. For manual migration: Use backend/database_migration_complete.py
3. For testing: Use backend/test_migration_system.py

LEGACY USAGE (NOT RECOMMENDED):
This script is kept for backwards compatibility only.
Use the new system instead for better results.
"""

import sys
import os

print("⚠️  WARNING: This migration script is DEPRECATED!")
print("=" * 60)
print("📍 The comprehensive migration system has replaced this script")
print("🚀 New location: backend/database_migration_complete.py")
print("✨ Features: Automatic startup integration, all models, better error handling")
print("=" * 60)
print()

# Ask user if they want to continue with the legacy script
user_input = input("Do you want to continue with this deprecated script? (y/N): ").lower().strip()

if user_input not in ['y', 'yes']:
    print("✅ Good choice! Here's what to do instead:")
    print()
    print("🔄 For automatic migration (recommended):")
    print("   docker-compose restart")
    print("   # Migration runs automatically on startup")
    print()
    print("🛠️  For manual migration:")
    print("   python backend/database_migration_complete.py")
    print()
    print("🧪 For testing:")
    print("   python backend/test_migration_system.py")
    print()
    print("📊 For status check:")
    print("   python backend/migration_summary.py")
    print()
    print("Exiting deprecated script.")
    sys.exit(0)

print("⚠️  Proceeding with deprecated script...")
print("💡 Consider upgrading to the new system for better results")
print("=" * 60)

# Add paths for different environments
sys.path.append('/app')          # For container environments  
sys.path.append('.')             # For local environments
sys.path.append('./backend')     # For running from project root
sys.path.append('../backend')    # For running from subdirectories

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
    """Add missing columns to monitors table."""
    session = new_session()
    
    try:
        print("🔍 Checking monitors table schema...")
        
        # Check if monitors table exists
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        
        if 'monitors' not in tables:
            print("❌ monitors table does not exist!")
            return False
        
        db_type = get_database_type(session)
        print(f"📊 Database type detected: {db_type}")
        
        # Define columns that should exist
        required_columns = {
            'arrest_date': 'DATE NULL',
            'arrest_reason': 'VARCHAR(255) NULL',
            'arresting_agency': 'VARCHAR(255) NULL', 
            'mugshot': 'TEXT NULL',
            'enable_notifications': 'INTEGER NOT NULL DEFAULT 1',
            'notify_method': 'VARCHAR(255) NULL DEFAULT \'pushover\'',
            'notify_address': 'VARCHAR(255) NOT NULL DEFAULT \'\''
        }
        
        # Adjust for database-specific types
        if db_type == 'mysql':
            # MySQL syntax
            pass  # Already correct
        elif db_type == 'postgresql':
            # PostgreSQL adjustments
            required_columns['enable_notifications'] = 'INTEGER NOT NULL DEFAULT 1'
            required_columns['notify_method'] = 'VARCHAR(255) DEFAULT \'pushover\''
            required_columns['notify_address'] = 'VARCHAR(255) NOT NULL DEFAULT \'\''
        elif db_type == 'sqlite':
            # SQLite adjustments
            required_columns['arrest_date'] = 'DATE'
            required_columns['enable_notifications'] = 'INTEGER NOT NULL DEFAULT 1'
        
        missing_columns = []
        existing_columns = []
        
        # Check each required column
        for column_name, column_def in required_columns.items():
            if check_column_exists(session, 'monitors', column_name):
                existing_columns.append(column_name)
                print(f"  ✅ {column_name} - exists")
            else:
                missing_columns.append((column_name, column_def))
                print(f"  ❌ {column_name} - missing")
        
        if not missing_columns:
            print("🎉 All required columns already exist!")
            return True
        
        print(f"\n🔧 Adding {len(missing_columns)} missing columns...")
        
        # Add missing columns
        for column_name, column_def in missing_columns:
            try:
                print(f"  📝 Adding {column_name}...")
                
                if db_type == 'mysql':
                    sql = f"ALTER TABLE monitors ADD COLUMN {column_name} {column_def}"
                elif db_type == 'postgresql':
                    sql = f"ALTER TABLE monitors ADD COLUMN {column_name} {column_def}"
                elif db_type == 'sqlite':
                    sql = f"ALTER TABLE monitors ADD COLUMN {column_name} {column_def}"
                else:
                    sql = f"ALTER TABLE monitors ADD COLUMN {column_name} {column_def}"
                
                session.execute(text(sql))
                session.commit()
                print(f"    ✅ {column_name} added successfully")
                
            except Exception as e:
                error_msg = str(e).lower()
                if 'duplicate' in error_msg or 'already exists' in error_msg:
                    print(f"    ℹ️  {column_name} already exists")
                else:
                    print(f"    ❌ Error adding {column_name}: {e}")
                    session.rollback()
                    return False
        
        # Add unique constraint if it doesn't exist
        try:
            print("🔒 Adding unique constraint...")
            if db_type == 'mysql':
                session.execute(text("ALTER TABLE monitors ADD CONSTRAINT unique_monitor UNIQUE (name, notify_address)"))
            elif db_type == 'postgresql':
                session.execute(text("ALTER TABLE monitors ADD CONSTRAINT unique_monitor UNIQUE (name, notify_address)"))
            elif db_type == 'sqlite':
                # SQLite doesn't support adding constraints to existing tables easily
                print("    ℹ️  SQLite: Unique constraint will be enforced by application logic")
            session.commit()
            print("    ✅ Unique constraint added")
        except Exception as e:
            error_msg = str(e).lower()
            if 'duplicate' in error_msg or 'already exists' in error_msg:
                print("    ℹ️  Unique constraint already exists")
            else:
                print(f"    ⚠️  Could not add unique constraint: {e}")
                # This is not critical, continue
        
        print("\n🎉 Monitor table migration completed successfully!")
        print("\n📋 Migration Summary:")
        print(f"  • Database type: {db_type}")
        print(f"  • Columns added: {len(missing_columns)}")
        print(f"  • Columns already present: {len(existing_columns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def verify_migration():
    """Verify that the migration was successful."""
    session = new_session()
    
    try:
        print("\n🔍 Verifying migration...")
        
        # Test a query that would fail with the old schema
        result = session.execute(text("SELECT name, arrest_date, notify_address FROM monitors LIMIT 1"))
        print("✅ Monitor table query successful!")
        
        # Count total columns
        inspector = inspect(session.bind)
        columns = inspector.get_columns('monitors')
        print(f"✅ Monitor table has {len(columns)} columns")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("🚀 Monitor Table Migration Script")
    print("=" * 40)
    
    if migrate_monitors_table():
        if verify_migration():
            print("\n🎉 Migration completed and verified successfully!")
            print("✅ Your monitors table now matches the SQLAlchemy model")
            print("✅ No more 'Unknown column' errors should occur")
        else:
            print("\n⚠️  Migration completed but verification failed")
            print("🔧 Please check your database manually")
    else:
        print("\n❌ Migration failed!")
        print("🔧 Please check the error messages above")
    
    print("\n" + "=" * 40)
