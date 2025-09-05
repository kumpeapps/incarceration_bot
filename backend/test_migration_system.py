#!/usr/bin/env python3
"""
Quick Test of Migration System
Tests the comprehensive database migration without making changes
"""

import sys
import os
import logging

# Add paths for different environments
sys.path.append('/app')
sys.path.append('.')
sys.path.append('./backend')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_migration_imports():
    """Test that all migration modules can be imported."""
    logger.info("🧪 Testing migration module imports...")
    
    try:
        from database_migration_complete import CompleteDatabaseMigrator
        logger.info("  ✅ database_migration_complete imported successfully")
    except ImportError as e:
        logger.error(f"  ❌ Failed to import database_migration_complete: {e}")
        return False
    
    try:
        from schema_migrator import DatabaseSchemaMigrator
        logger.info("  ✅ schema_migrator imported successfully")
    except ImportError as e:
        logger.error(f"  ❌ Failed to import schema_migrator: {e}")
        return False
    
    try:
        from database_connect import new_session
        logger.info("  ✅ database_connect imported successfully")
    except ImportError as e:
        logger.error(f"  ❌ Failed to import database_connect: {e}")
        return False
    
    return True

def test_model_imports():
    """Test that all models can be imported."""
    logger.info("🧪 Testing model imports...")
    
    models_to_test = [
        'User', 'Group', 'UserGroup', 'Jail', 'Inmate', 
        'Monitor', 'MonitorLink', 'MonitorInmateLink', 'Session'
    ]
    
    success = True
    
    for model_name in models_to_test:
        try:
            module = __import__(f'models.{model_name}', fromlist=[model_name])
            model_class = getattr(module, model_name)
            logger.info(f"  ✅ {model_name} imported successfully")
            
            # Check if it has required attributes
            if hasattr(model_class, '__tablename__'):
                logger.info(f"    📋 Table name: {model_class.__tablename__}")
            else:
                logger.warning(f"    ⚠️  {model_name} missing __tablename__")
                
        except ImportError as e:
            logger.error(f"  ❌ Failed to import {model_name}: {e}")
            success = False
        except Exception as e:
            logger.error(f"  ❌ Error with {model_name}: {e}")
            success = False
    
    return success

def test_database_connection():
    """Test database connection."""
    logger.info("🧪 Testing database connection...")
    
    try:
        from database_connect import new_session
        session = new_session()
        
        # Test basic query
        from sqlalchemy import text
        session.execute(text("SELECT 1"))
        
        session.close()
        logger.info("  ✅ Database connection successful")
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Database connection failed: {e}")
        return False

def run_migration_dry_run():
    """Run migration in dry-run mode to check for issues."""
    logger.info("🧪 Running migration dry-run...")
    
    try:
        from database_migration_complete import CompleteDatabaseMigrator
        
        # Create migrator but don't run full migration
        migrator = CompleteDatabaseMigrator()
        
        if migrator.connect_database():
            try:
                # Just run verification to see current state
                logger.info("  🔍 Running verification queries...")
                migrator.verify_critical_queries()
                logger.info("  ✅ Dry-run completed")
                return True
            finally:
                migrator.disconnect_database()
        else:
            logger.error("  ❌ Could not connect to database")
            return False
            
    except Exception as e:
        logger.error(f"  ❌ Dry-run failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("🚀 Starting Migration System Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Import Tests", test_migration_imports),
        ("Model Tests", test_model_imports),
        ("Database Tests", test_database_connection),
        ("Dry-Run Tests", run_migration_dry_run)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🏃 Running {test_name}...")
        try:
            if test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
    
    logger.info("=" * 50)
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Migration system is ready.")
        return True
    else:
        logger.error("⚠️  Some tests failed. Check issues before running migration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
