#!/usr/bin/env python3
"""
Migration System Summary and Quick Access Script
Provides easy access to all migration functionality and status overview
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Add paths for different environments
sys.path.append('/app')
sys.path.append('.')
sys.path.append('./backend')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_header():
    """Print system header."""
    print("=" * 70)
    print("🚀 INCARCERATION BOT DATABASE MIGRATION SYSTEM")
    print("=" * 70)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def print_system_status():
    """Print current system status."""
    print("📊 SYSTEM STATUS")
    print("-" * 30)
    
    # Check if migration modules are available
    migration_modules = {
        'database_migration_complete': False,
        'schema_migrator': False,
        'legacy_monitor_migration': False,
        'database_connect': False
    }
    
    for module_name in migration_modules.keys():
        try:
            __import__(module_name)
            migration_modules[module_name] = True
            print(f"✅ {module_name}")
        except ImportError:
            print(f"❌ {module_name}")
    
    print()
    
    # Check database connectivity
    print("🔌 DATABASE CONNECTIVITY")
    print("-" * 30)
    try:
        from database_connect import new_session
        session = new_session()
        from sqlalchemy import text
        session.execute(text("SELECT 1"))
        session.close()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    
    print()

def run_quick_verification():
    """Run quick verification of critical tables."""
    print("🔍 QUICK VERIFICATION")
    print("-" * 30)
    
    try:
        from database_migration_complete import CompleteDatabaseMigrator
        
        migrator = CompleteDatabaseMigrator()
        if migrator.connect_database():
            try:
                # Run verification
                success = migrator.verify_critical_queries()
                
                if success:
                    print("✅ All critical queries passed")
                else:
                    print("⚠️  Some verification issues found")
                    if migrator.verification_failures:
                        print("   Failed queries:")
                        for query_name, error in migrator.verification_failures:
                            print(f"     - {query_name}: {error}")
                
            finally:
                migrator.disconnect_database()
        else:
            print("❌ Could not connect to database")
    except Exception as e:
        print(f"❌ Verification failed: {e}")
    
    print()

def show_available_commands():
    """Show available migration commands."""
    print("🛠️  AVAILABLE COMMANDS")
    print("-" * 30)
    
    commands = [
        ("Complete Migration", "python backend/database_migration_complete.py"),
        ("Verification Only", "python backend/database_migration_complete.py --verify-only"),
        ("Force Sync", "python backend/database_migration_complete.py --force-sync"),
        ("Schema Migrator", "python backend/schema_migrator.py"),
        ("Test System", "python backend/test_migration_system.py"),
        ("Legacy Monitor", "python backend/legacy_monitor_migration.py"),
        ("This Summary", "python backend/migration_summary.py")
    ]
    
    for name, command in commands:
        print(f"📝 {name}:")
        print(f"   {command}")
        print()

def show_file_locations():
    """Show locations of migration files."""
    print("📁 FILE LOCATIONS")
    print("-" * 30)
    
    files = [
        ("Complete Migration System", "backend/database_migration_complete.py"),
        ("Modern Schema Migrator", "backend/schema_migrator.py"),
        ("Legacy Monitor Migration", "backend/legacy_monitor_migration.py"),
        ("Migration Test Suite", "backend/test_migration_system.py"),
        ("Integration (Startup)", "backend/init_db.py"),
        ("Migration Documentation", "backend/README_MIGRATION.md"),
        ("This Summary Script", "backend/migration_summary.py")
    ]
    
    for name, path in files:
        exists = "✅" if os.path.exists(path) else "❌"
        print(f"{exists} {name}: {path}")
    
    print()

def show_legacy_file_status():
    """Show status of legacy files that were moved."""
    print("📦 LEGACY FILE STATUS")
    print("-" * 30)
    
    legacy_files = [
        ("migrate_monitors_table.py", "Project root (deprecated)", "backend/legacy_monitor_migration.py"),
        ("force_schema_sync.py", "Project root (integrated)", "backend/database_migration_complete.py")
    ]
    
    for old_file, old_location, new_location in legacy_files:
        old_exists = "✅" if os.path.exists(old_file) else "❌"
        new_exists = "✅" if os.path.exists(new_location) else "❌"
        print(f"📄 {old_file}:")
        print(f"   Old: {old_exists} {old_location}")
        print(f"   New: {new_exists} {new_location}")
        print()

def main():
    """Main function with command line support."""
    parser = argparse.ArgumentParser(description='Migration System Summary and Quick Access')
    parser.add_argument('--verify', action='store_true', help='Run quick verification')
    parser.add_argument('--full-migration', action='store_true', help='Run complete migration')
    parser.add_argument('--test', action='store_true', help='Run test suite')
    
    args = parser.parse_args()
    
    print_header()
    
    if args.verify:
        run_quick_verification()
        return
    
    if args.full_migration:
        print("🚀 Running complete migration...")
        try:
            from database_migration_complete import CompleteDatabaseMigrator
            migrator = CompleteDatabaseMigrator()
            success = migrator.run_complete_migration()
            if success:
                print("🎉 Migration completed successfully!")
            else:
                print("❌ Migration failed!")
            return
        except Exception as e:
            print(f"❌ Migration error: {e}")
            return
    
    if args.test:
        print("🧪 Running test suite...")
        try:
            from test_migration_system import main as test_main
            test_main()
            return
        except Exception as e:
            print(f"❌ Test error: {e}")
            return
    
    # Default: show full summary
    print_system_status()
    run_quick_verification()
    show_available_commands()
    show_file_locations()
    show_legacy_file_status()
    
    print("💡 QUICK START")
    print("-" * 30)
    print("For most users:")
    print("  python backend/migration_summary.py --verify")
    print("  python backend/migration_summary.py --full-migration")
    print()
    print("For testing:")
    print("  python backend/migration_summary.py --test")
    print()
    print("=" * 70)

if __name__ == "__main__":
    main()
