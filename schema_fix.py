#!/usr/bin/env python3
"""
Simple script to add missing columns to users table.
Run this once on your remote server to fix the schema.
"""

import sys
sys.path.append('/app')

from database_connect import new_session
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_missing_columns():
    """Add missing columns to users table."""
    session = new_session()
    
    try:
        logger.info("Adding missing columns to users table...")
        
        # Add api_key column
        try:
            session.execute(text("ALTER TABLE users ADD COLUMN api_key VARCHAR(255) NULL"))
            logger.info("✅ Added api_key column")
        except Exception as e:
            if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                logger.info("✅ api_key column already exists")
            else:
                logger.error(f"Failed to add api_key: {e}")
                raise
        
        # Add amember_user_id column
        try:
            session.execute(text("ALTER TABLE users ADD COLUMN amember_user_id INT NULL"))
            logger.info("✅ Added amember_user_id column")
        except Exception as e:
            if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                logger.info("✅ amember_user_id column already exists")
            else:
                logger.error(f"Failed to add amember_user_id: {e}")
                raise
        
        # Add password_format column
        try:
            session.execute(text("ALTER TABLE users ADD COLUMN password_format VARCHAR(20) NOT NULL DEFAULT 'bcrypt'"))
            logger.info("✅ Added password_format column")
        except Exception as e:
            if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                logger.info("✅ password_format column already exists")
            else:
                logger.error(f"Failed to add password_format: {e}")
                raise
        
        # Add unique constraints
        try:
            session.execute(text("ALTER TABLE users ADD CONSTRAINT uk_users_api_key UNIQUE (api_key)"))
            logger.info("✅ Added unique constraint for api_key")
        except Exception as e:
            if 'duplicate' in str(e).lower() or 'already exists' in str(e).lower():
                logger.info("✅ api_key unique constraint already exists")
            else:
                logger.warning(f"Could not add api_key unique constraint: {e}")
        
        try:
            session.execute(text("ALTER TABLE users ADD CONSTRAINT uk_users_amember_user_id UNIQUE (amember_user_id)"))
            logger.info("✅ Added unique constraint for amember_user_id")
        except Exception as e:
            if 'duplicate' in str(e).lower() or 'already exists' in str(e).lower():
                logger.info("✅ amember_user_id unique constraint already exists")
            else:
                logger.warning(f"Could not add amember_user_id unique constraint: {e}")
        
        session.commit()
        logger.info("🎉 All schema updates completed successfully!")
        
        # Verify the columns exist
        from sqlalchemy import inspect
        inspector = inspect(session.bind)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        required = ['api_key', 'amember_user_id', 'password_format']
        missing = [col for col in required if col not in columns]
        
        if missing:
            logger.error(f"❌ Still missing columns: {', '.join(missing)}")
            return False
        else:
            logger.info("✅ All required columns are now present!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Schema update failed: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("🔧 Adding missing columns to users table...")
    success = add_missing_columns()
    if success:
        print("\n✅ Schema fix completed! Your aMember plugin should now work.")
        sys.exit(0)
    else:
        print("\n❌ Schema fix failed!")
        sys.exit(1)
