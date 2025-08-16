#!/usr/bin/env python3
"""
Force Database Schema Sync
This script ensures the database schema matches the expected state regardless of Alembic history.
"""

import sys
import os
sys.path.append('/app')

from database_connect import get_db
from sqlalchemy import inspect, text, Column, String, Integer
from sqlalchemy.exc import OperationalError

def ensure_users_table_schema():
    """Ensure users table has all required columns with proper types."""
    
    db = next(get_db())
    try:
        inspector = inspect(db.bind)
        
        # Check if users table exists
        tables = inspector.get_table_names()
        if 'users' not in tables:
            print("❌ Users table does not exist!")
            return False
            
        # Get current columns
        columns = inspector.get_columns('users')
        column_names = [col['name'] for col in columns]
        
        print("📋 Current users table columns:")
        for col in sorted(column_names):
            print(f"   ✓ {col}")
        
        # Define required columns and their specifications
        required_columns = {
            'api_key': {
                'type': 'VARCHAR(255)',
                'nullable': True,
                'unique': True
            },
            'amember_user_id': {
                'type': 'INTEGER',
                'nullable': True,
                'unique': True
            },
            'password_format': {
                'type': 'VARCHAR(20)',
                'nullable': False,
                'default': "'bcrypt'"
            }
        }
        
        # Check and add missing columns
        missing_columns = []
        dialect_name = db.bind.dialect.name
        
        for column_name, spec in required_columns.items():
            if column_name not in column_names:
                missing_columns.append(column_name)
                print(f"➕ Adding missing column: {column_name}")
                
                # Get database-specific type
                if dialect_name == 'mysql':
                    db_type = spec['type']
                elif dialect_name == 'postgresql':
                    db_type = spec['type'].replace('VARCHAR', 'VARCHAR')
                elif dialect_name == 'sqlite':
                    db_type = 'TEXT' if 'VARCHAR' in spec['type'] else 'INTEGER'
                else:
                    db_type = spec['type']
                
                # Build ALTER TABLE statement
                nullable = 'NULL' if spec['nullable'] else 'NOT NULL'
                default_clause = f" DEFAULT {spec['default']}" if 'default' in spec else ""
                
                sql = f"ALTER TABLE users ADD COLUMN {column_name} {db_type} {nullable}{default_clause}"
                
                try:
                    db.execute(text(sql))
                    print(f"✅ Added column {column_name}")
                    
                    # Add unique constraint if specified
                    if spec.get('unique'):
                        try:
                            constraint_name = f"uk_users_{column_name}"
                            constraint_sql = f"ALTER TABLE users ADD CONSTRAINT {constraint_name} UNIQUE ({column_name})"
                            db.execute(text(constraint_sql))
                            print(f"✅ Added unique constraint for {column_name}")
                        except OperationalError as e:
                            if 'duplicate' not in str(e).lower() and 'already exists' not in str(e).lower():
                                print(f"⚠️  Could not add unique constraint for {column_name}: {e}")
                    
                except OperationalError as e:
                    if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                        print(f"✅ Column {column_name} already exists (detected during add)")
                    else:
                        print(f"❌ Failed to add column {column_name}: {e}")
                        return False
        
        db.commit()
        
        # Verify final state
        print("\n📋 Final verification:")
        inspector = inspect(db.bind)
        final_columns = [col['name'] for col in inspector.get_columns('users')]
        
        all_present = True
        for column_name in required_columns.keys():
            if column_name in final_columns:
                print(f"✅ {column_name} - PRESENT")
            else:
                print(f"❌ {column_name} - MISSING")
                all_present = False
        
        if all_present:
            print("\n🎉 ALL REQUIRED COLUMNS PRESENT - Schema sync successful!")
            
            # Update Alembic version to current head to prevent future issues
            try:
                db.execute(text("UPDATE alembic_version SET version_num = 'a9f5f7465f50'"))
                db.commit()
                print("✅ Updated Alembic version to current head")
            except Exception as e:
                print(f"⚠️  Could not update Alembic version: {e}")
            
            return True
        else:
            print("\n❌ Some columns still missing after sync")
            return False
            
    except Exception as e:
        print(f"❌ Error during schema sync: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 FORCE DATABASE SCHEMA SYNC")
    print("============================")
    
    success = ensure_users_table_schema()
    
    if success:
        print("\n✅ Schema sync completed successfully!")
        print("🔗 Your aMember plugin should now work correctly.")
        sys.exit(0)
    else:
        print("\n❌ Schema sync failed!")
        print("📋 Manual database intervention required.")
        sys.exit(1)
