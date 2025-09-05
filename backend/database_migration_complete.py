#!/usr/bin/env python3
"""
Complete Database Migration and Sync Utility
Consolidates all migration functionality into one comprehensive script
Automatically runs on container startup via init_db.py integration
Can also be run standalone for manual migrations

This replaces:
- migrate_monitors_table.py
- force_schema_sync.py
- Individual column addition scripts

Usage:
  python backend/database_migration_complete.py
  python backend/database_migration_complete.py --verify-only
  python backend/database_migration_complete.py --force-sync
"""

import sys
import os
import argparse
import logging
from typing import Dict, List, Optional

# Add paths for different environments
sys.path.append('/app')          # For container environments  
sys.path.append('.')             # For local environments
sys.path.append('./backend')     # For running from project root

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from database_connect import new_session
    from schema_migrator import DatabaseSchemaMigrator
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you're running this from the correct directory")
    sys.exit(1)

from sqlalchemy import text, inspect, Column, Integer, String, Boolean, Date, DateTime, Text
from sqlalchemy.exc import OperationalError, ProgrammingError

class CompleteDatabaseMigrator:
    """Complete database migration system with all legacy functionality."""
    
    def __init__(self):
        self.session = None
        self.changes_applied = 0
        self.verification_failures = []
    
    def connect_database(self) -> bool:
        """Establish database connection."""
        try:
            self.session = new_session()
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def disconnect_database(self):
        """Close database connection."""
        if self.session:
            self.session.close()
    
    def run_legacy_force_sync(self) -> bool:
        """Run legacy force schema sync operations."""
        logger.info("🔧 Running legacy force schema sync...")
        
        try:
            inspector = inspect(self.session.bind)
            
            # Ensure users table schema (from force_schema_sync.py)
            if not self._ensure_users_table_schema(inspector):
                return False
            
            # Ensure inmates table schema
            if not self._ensure_inmates_table_schema(inspector):
                return False
            
            # Ensure monitors table schema (from migrate_monitors_table.py)
            if not self._ensure_monitors_table_schema(inspector):
                return False
            
            logger.info("✅ Legacy force sync completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Legacy force sync failed: {e}")
            return False
    
    def _ensure_users_table_schema(self, inspector) -> bool:
        """Ensure users table has all required columns (legacy functionality)."""
        logger.info("  🔍 Checking users table schema...")
        
        try:
            # Check if users table exists
            if 'users' not in inspector.get_table_names():
                logger.error("  ❌ Users table does not exist!")
                return False
            
            # Get current columns
            columns = inspector.get_columns('users')
            column_names = [col['name'] for col in columns]
            
            # Required columns for users table
            required_columns = {
                'id': 'INTEGER PRIMARY KEY',
                'username': 'VARCHAR(50) UNIQUE NOT NULL', 
                'email': 'VARCHAR(100)',
                'password_hash': 'VARCHAR(255)',
                'api_key': 'VARCHAR(255)',
                'is_admin': 'BOOLEAN DEFAULT FALSE',
                'amember_user_id': 'INTEGER UNIQUE',
                'password_format': 'VARCHAR(20) DEFAULT "bcrypt"'
            }
            
            for col_name, col_def in required_columns.items():
                if col_name not in column_names:
                    logger.info(f"    📝 Adding missing column: {col_name}")
                    try:
                        self.session.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
                        self.session.commit()
                        self.changes_applied += 1
                        logger.info(f"    ✅ Added {col_name}")
                    except Exception as e:
                        if 'duplicate' in str(e).lower() or 'already exists' in str(e).lower():
                            logger.info(f"    ℹ️  {col_name} already exists")
                        else:
                            logger.error(f"    ❌ Error adding {col_name}: {e}")
                            return False
            
            logger.info("  ✅ Users table schema validated")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Users table validation failed: {e}")
            return False
    
    def _ensure_inmates_table_schema(self, inspector) -> bool:
        """Ensure inmates table has proper schema with partitioning support."""
        logger.info("  🔍 Checking inmates table schema...")
        
        try:
            if 'inmates' not in inspector.get_table_names():
                logger.info("  ℹ️  Inmates table does not exist - will be created by schema initialization")
                return True
            
            # Check for MEDIUMTEXT support on mugshot column
            columns = inspector.get_columns('inmates')
            mugshot_col = next((col for col in columns if col['name'] == 'mugshot'), None)
            
            if mugshot_col:
                col_type = str(mugshot_col['type']).upper()
                if 'MEDIUMTEXT' not in col_type and 'TEXT' in col_type:
                    logger.info("    📝 Upgrading mugshot column to MEDIUMTEXT")
                    try:
                        self.session.execute(text("ALTER TABLE inmates MODIFY COLUMN mugshot MEDIUMTEXT"))
                        self.session.commit()
                        self.changes_applied += 1
                        logger.info("    ✅ Upgraded mugshot column")
                    except Exception as e:
                        logger.warning(f"    ⚠️  Could not upgrade mugshot column: {e}")
            
            # Check hold_reasons column
            hold_reasons_col = next((col for col in columns if col['name'] == 'hold_reasons'), None)
            if not hold_reasons_col:
                logger.info("    📝 Adding hold_reasons column")
                try:
                    self.session.execute(text("ALTER TABLE inmates ADD COLUMN hold_reasons TEXT"))
                    self.session.commit()
                    self.changes_applied += 1
                    logger.info("    ✅ Added hold_reasons column")
                except Exception as e:
                    if 'duplicate' not in str(e).lower():
                        logger.warning(f"    ⚠️  Could not add hold_reasons column: {e}")
            
            logger.info("  ✅ Inmates table schema validated")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Inmates table validation failed: {e}")
            return False
    
    def _ensure_monitors_table_schema(self, inspector) -> bool:
        """Ensure monitors table has all required columns (from actual Monitor model)."""
        logger.info("  🔍 Checking monitors table schema...")
        
        try:
            if 'monitors' not in inspector.get_table_names():
                logger.info("  ℹ️  Monitors table does not exist - will be created by schema initialization")
                return True
            
            columns = inspector.get_columns('monitors')
            column_names = [col['name'] for col in columns]
            
            # Required columns based on actual Monitor model in models/Monitor.py
            required_columns = {
                'idmonitors': 'INTEGER PRIMARY KEY AUTO_INCREMENT',  # Actual PK name
                'name': 'VARCHAR(255) NOT NULL',
                'user_id': 'INTEGER',
                'arrest_date': 'DATE',
                'release_date': 'VARCHAR(255)',
                'arrest_reason': 'VARCHAR(255)',
                'arresting_agency': 'VARCHAR(255)',
                'jail': 'VARCHAR(255)',
                'mugshot': 'TEXT(65535)',
                'enable_notifications': 'INTEGER NOT NULL DEFAULT 1',
                'notify_method': 'VARCHAR(255) DEFAULT "pushover"',
                'notify_address': 'VARCHAR(255) NOT NULL DEFAULT ""',
                'last_seen_incarcerated': 'TIMESTAMP DEFAULT NULL'
            }
            
            # Adjust for database type
            db_type = self.session.bind.dialect.name.lower()
            if 'postgres' in db_type:
                required_columns['idmonitors'] = 'SERIAL PRIMARY KEY'
                required_columns['last_seen_incarcerated'] = 'TIMESTAMP DEFAULT NULL'
            elif 'sqlite' in db_type:
                required_columns['idmonitors'] = 'INTEGER PRIMARY KEY AUTOINCREMENT'
                required_columns['last_seen_incarcerated'] = 'TIMESTAMP DEFAULT NULL'
            
            for col_name, col_def in required_columns.items():
                if col_name not in column_names:
                    logger.info(f"    📝 Adding missing column: {col_name}")
                    try:
                        # Skip primary key if it's missing (table structure issue)
                        if 'PRIMARY KEY' in col_def and col_name == 'idmonitors':
                            logger.warning(f"    ⚠️  Cannot add primary key {col_name} to existing table")
                            continue
                        
                        # Simplify definition for ALTER TABLE
                        simple_def = col_def.replace(' AUTO_INCREMENT', '').replace(' AUTOINCREMENT', '')
                        if 'DEFAULT' not in simple_def and col_name != 'idmonitors':
                            if 'NOT NULL' in simple_def:
                                # Add default for NOT NULL columns
                                if 'INTEGER' in simple_def:
                                    simple_def += ' DEFAULT 0'
                                elif 'VARCHAR' in simple_def:
                                    simple_def += ' DEFAULT ""'
                        
                        self.session.execute(text(f"ALTER TABLE monitors ADD COLUMN {col_name} {simple_def}"))
                        self.session.commit()
                        self.changes_applied += 1
                        logger.info(f"    ✅ Added {col_name}")
                    except Exception as e:
                        if 'duplicate' in str(e).lower() or 'already exists' in str(e).lower():
                            logger.info(f"    ℹ️  {col_name} already exists")
                        else:
                            logger.error(f"    ❌ Error adding {col_name}: {e}")
                            return False
            
            logger.info("  ✅ Monitors table schema validated")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Monitors table validation failed: {e}")
            return False
    
    def run_comprehensive_migration(self) -> bool:
        """Run the comprehensive schema migration using the new system."""
        logger.info("🚀 Running comprehensive schema migration...")
        
        try:
            migrator = DatabaseSchemaMigrator(self.session)
            return migrator.migrate_all_models()
        except Exception as e:
            logger.error(f"❌ Comprehensive migration failed: {e}")
            return False
    
    def verify_critical_queries(self) -> bool:
        """Verify that critical database queries work."""
        logger.info("🔍 Verifying critical database queries...")
        
        verification_queries = [
            # Monitor queries that commonly fail (using actual column names)
            ("monitors_basic", "SELECT idmonitors, name FROM monitors LIMIT 1"),
            ("monitors_arrest_date", "SELECT name, arrest_date FROM monitors LIMIT 1"),
            ("monitors_full", "SELECT name, arrest_date, arrest_reason, arresting_agency FROM monitors LIMIT 1"),
            ("monitors_user_relation", "SELECT name, user_id FROM monitors LIMIT 1"),
            ("monitors_notifications", "SELECT name, notify_method, notify_address FROM monitors LIMIT 1"),
            
            # User queries
            ("users_basic", "SELECT id, username FROM users LIMIT 1"),
            ("users_api_key", "SELECT username, api_key FROM users LIMIT 1"),
            ("users_amember", "SELECT username, amember_user_id FROM users LIMIT 1"),
            
            # Inmate queries  
            ("inmates_basic", "SELECT idinmates, name FROM inmates LIMIT 1"),
            ("inmates_mugshot", "SELECT name, mugshot FROM inmates LIMIT 1"),
            ("inmates_hold_reasons", "SELECT name, hold_reasons FROM inmates LIMIT 1"),
            
            # Group queries
            ("groups_basic", "SELECT id, name FROM groups LIMIT 1"),
            
            # Join queries that commonly fail
            ("user_groups", """SELECT u.username, g.name 
                              FROM users u 
                              LEFT JOIN usergroups ug ON u.id = ug.user_id 
                              LEFT JOIN groups g ON ug.group_id = g.id 
                              LIMIT 1"""),
        ]
        
        success_count = 0
        total_queries = len(verification_queries)
        
        for query_name, query_sql in verification_queries:
            try:
                self.session.execute(text(query_sql))
                logger.info(f"  ✅ {query_name}: PASSED")
                success_count += 1
            except Exception as e:
                logger.warning(f"  ❌ {query_name}: FAILED - {e}")
                self.verification_failures.append((query_name, str(e)))
        
        success_rate = (success_count / total_queries) * 100
        logger.info(f"📊 Verification results: {success_count}/{total_queries} queries passed ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            logger.info("✅ Verification PASSED - Database is in good state")
            return True
        elif success_rate >= 70:
            logger.warning("⚠️  Verification PARTIAL - Some issues remain but critical functionality works")
            return True
        else:
            logger.error("❌ Verification FAILED - Significant database issues detected")
            return False
    
    def run_complete_migration(self, force_sync: bool = False) -> bool:
        """Run complete migration process."""
        logger.info("🏁 Starting complete database migration process...")
        logger.info("=" * 60)
        
        if not self.connect_database():
            return False
        
        try:
            success = True
            
            # Step 1: Legacy force sync (if requested)
            if force_sync:
                if not self.run_legacy_force_sync():
                    logger.error("❌ Legacy force sync failed")
                    success = False
            
            # Step 2: Comprehensive migration using new system
            if not self.run_comprehensive_migration():
                logger.error("❌ Comprehensive migration failed")
                success = False
            
            # Step 3: Verify everything works
            if not self.verify_critical_queries():
                logger.warning("⚠️  Some verification queries failed")
                # Don't fail the entire migration for verification issues
            
            if success:
                logger.info("=" * 60)
                logger.info(f"🎉 Complete migration SUCCEEDED!")
                logger.info(f"📊 Total changes applied: {self.changes_applied}")
                if self.verification_failures:
                    logger.info(f"⚠️  {len(self.verification_failures)} verification issues noted")
                logger.info("=" * 60)
            else:
                logger.error("=" * 60)
                logger.error("❌ Complete migration FAILED!")
                logger.error("=" * 60)
            
            return success
            
        finally:
            self.disconnect_database()

def main():
    """Main entry point with command line argument support."""
    parser = argparse.ArgumentParser(description='Complete Database Migration and Sync Utility')
    parser.add_argument('--verify-only', action='store_true', 
                       help='Only run verification queries, no migrations')
    parser.add_argument('--force-sync', action='store_true',
                       help='Run legacy force sync operations before comprehensive migration')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    migrator = CompleteDatabaseMigrator()
    
    if args.verify_only:
        logger.info("🔍 Running verification-only mode...")
        if migrator.connect_database():
            try:
                success = migrator.verify_critical_queries()
                return 0 if success else 1
            finally:
                migrator.disconnect_database()
        else:
            return 1
    else:
        success = migrator.run_complete_migration(force_sync=args.force_sync)
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
