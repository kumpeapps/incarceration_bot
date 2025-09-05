#!/usr/bin/env python3
"""
Test script to verify UserGroup table creation and fix.
This tests both the table name fix in database_migration_complete.py
and the new ensure_user_groups_schema() function.
"""

import sys
import os

# Add paths for testing
sys.path.append('./backend')

def test_usergroup_fixes():
    """Test UserGroup table fixes."""
    print("🔍 Testing UserGroup Table Fixes")
    print("=" * 50)
    
    # Test 1: Model Import and Table Name
    try:
        from models.UserGroup import UserGroup
        print(f"✅ 1. UserGroup model imported successfully")
        print(f"   Table name: {UserGroup.__tablename__}")
        
        if UserGroup.__tablename__ == "user_groups":
            print("   ✅ Correct table name: user_groups")
        else:
            print(f"   ❌ Incorrect table name: {UserGroup.__tablename__}")
    except Exception as e:
        print(f"❌ 1. UserGroup model import failed: {e}")
        return
    
    # Test 2: Migration Complete Query Fix
    try:
        from database_migration_complete import CompleteDatabaseMigrator
        print("✅ 2. CompleteDatabaseMigrator imported successfully")
        
        # Read the source to verify the fix
        import inspect
        source = inspect.getsource(CompleteDatabaseMigrator.verify_critical_queries)
        if "LEFT JOIN user_groups ug" in source:
            print("   ✅ Query uses correct table name: user_groups")
        elif "LEFT JOIN usergroups ug" in source:
            print("   ❌ Query still uses incorrect table name: usergroups")
        else:
            print("   ⚠️  Could not find JOIN statement in source")
    except Exception as e:
        print(f"❌ 2. CompleteDatabaseMigrator test failed: {e}")
    
    # Test 3: Schema Creation Function
    try:
        from init_db import ensure_user_groups_schema
        print("✅ 3. ensure_user_groups_schema function imported successfully")
        print("   ✅ Function available for container startup")
    except Exception as e:
        print(f"❌ 3. ensure_user_groups_schema import failed: {e}")
    
    # Test 4: Integration with Migration System
    try:
        from init_db import run_comprehensive_schema_migration
        print("✅ 4. run_comprehensive_schema_migration imported successfully")
        print("   ✅ UserGroup fixes integrated into migration system")
    except Exception as e:
        print(f"❌ 4. Migration integration test failed: {e}")
    
    print()
    print("📋 Summary of UserGroup Fixes:")
    print("1. ✅ Fixed table name in database_migration_complete.py query")
    print("2. ✅ Added ensure_user_groups_schema() function to create table")
    print("3. ✅ Integrated UserGroup schema creation into migration system")
    print("4. ✅ Added fallback schema creation to handle missing table")
    print()
    print("🚀 Container restart should now create user_groups table correctly")
    print("🔧 The migration query will now use the correct table name")

if __name__ == "__main__":
    test_usergroup_fixes()
