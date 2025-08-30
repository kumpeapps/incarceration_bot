#!/usr/bin/env python3
"""
Populate missing last_seen dates for existing records
"""

import sys
from datetime import datetime
from database_connect import new_session
from sqlalchemy import text
import logging
import os

# Configure logging with environment variable support
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, LOG_LEVEL, logging.INFO)

logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def populate_last_seen():
    """Populate NULL last_seen values with current timestamp"""
    try:
        session = new_session()
        
        # Check how many records need updating
        result = session.execute(text("SELECT COUNT(*) FROM inmates WHERE last_seen IS NULL"))
        null_count = result.fetchone()[0]
        
        if null_count == 0:
            logger.info("All records already have last_seen values")
            session.close()
            return True
            
        logger.info(f"Updating {null_count:,} records with missing last_seen values")
        
        # Update all NULL last_seen to current timestamp
        result = session.execute(text("""
            UPDATE inmates 
            SET last_seen = NOW() 
            WHERE last_seen IS NULL
        """))
        
        updated_count = result.rowcount
        session.commit()
        
        logger.info(f"✓ Updated {updated_count:,} records successfully")
        
        # Verify results
        result = session.execute(text("SELECT COUNT(*) FROM inmates WHERE last_seen IS NULL"))
        remaining_null = result.fetchone()[0]
        
        logger.info(f"Records still with NULL last_seen: {remaining_null}")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to populate last_seen: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

if __name__ == "__main__":
    success = populate_last_seen()
    sys.exit(0 if success else 1)
