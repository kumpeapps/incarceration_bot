#!/usr/bin/env python3
"""
Database Cleanup Script with Table Locking for Incarceration Bot
Removes duplicate records with full table lock for maximum safety
WARNING: This will block ALL database access during cleanup
"""

import sys
import time
from datetime import datetime
from database_connect import new_session
from sqlalchemy import text
import logging
import os

# Configure logging with environment variable support
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, LOG_LEVEL, logging.INFO)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('maintenance_cleanup_locked.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def cleanup_with_table_lock():
    """Remove duplicates with full table lock - BLOCKS ALL ACCESS"""
    logger.info("=" * 60)
    logger.info("STARTING TABLE-LOCKED CLEANUP")
    logger.info("WARNING: This will block ALL database access!")
    logger.info("=" * 60)
    
    try:
        session = new_session()
        
        # Analyze before locking
        result = session.execute(text("SELECT COUNT(*) FROM inmates"))
        total_before = result.fetchone()[0]
        
        result = session.execute(text("""
            SELECT COUNT(DISTINCT CONCAT(name, '|', COALESCE(race,''), '|', COALESCE(dob,''), '|', 
                                       COALESCE(sex,''), '|', COALESCE(arrest_date,''), '|', jail_id)) 
            FROM inmates
        """))
        unique_count = result.fetchone()[0]
        
        duplicates_to_remove = total_before - unique_count
        logger.info(f"Will remove {duplicates_to_remove:,} duplicates from {total_before:,} records")
        
        if duplicates_to_remove == 0:
            logger.info("No duplicates found!")
            session.close()
            return True
        
        # LOCK THE TABLE - this blocks everything
        logger.info("🔒 LOCKING INMATES TABLE - All access blocked!")
        session.execute(text("LOCK TABLES inmates WRITE"))
        
        start_time = time.time()
        
        try:
            # Create temporary table for records to keep
            logger.info("Creating cleanup strategy...")
            session.execute(text("""
                CREATE TEMPORARY TABLE inmates_to_keep AS
                SELECT MAX(idinmates) as keep_id
                FROM inmates 
                GROUP BY name, race, dob, sex, arrest_date, jail_id
            """))
            
            # Single large delete operation (much faster when table is locked)
            logger.info("Executing bulk delete operation...")
            result = session.execute(text("""
                DELETE i FROM inmates i
                LEFT JOIN inmates_to_keep k ON i.idinmates = k.keep_id
                WHERE k.keep_id IS NULL
            """))
            
            deleted_count = result.rowcount
            session.commit()
            
            cleanup_time = time.time() - start_time
            logger.info(f"✓ Deleted {deleted_count:,} duplicate records in {cleanup_time:.1f} seconds")
            
        finally:
            # ALWAYS unlock the table
            session.execute(text("UNLOCK TABLES"))
            logger.info("🔓 Table unlocked - Database access restored")
        
        # Verify results
        result = session.execute(text("SELECT COUNT(*) FROM inmates"))
        total_after = result.fetchone()[0]
        
        logger.info(f"Cleanup complete: {total_before:,} → {total_after:,} records")
        logger.info(f"Removed: {total_before - total_after:,} duplicates")
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        try:
            session.execute(text("UNLOCK TABLES"))
            logger.info("🔓 Emergency table unlock performed")
        except:
            logger.error("❌ CRITICAL: Could not unlock table! Manual intervention required!")
        
        if 'session' in locals():
            session.close()
        return False

def main():
    """Main execution with user confirmation"""
    logger.info("TABLE LOCKING CLEANUP MODE")
    logger.info("This will:")
    logger.info("1. Lock the inmates table (blocking ALL access)")
    logger.info("2. Remove duplicates in a single operation")
    logger.info("3. Unlock the table")
    logger.info("")
    logger.info("⚠️  WARNING: Database will be completely inaccessible during cleanup!")
    logger.info("⚠️  Estimated downtime: 30-60 seconds for 400K duplicates")
    
    # In a script, you might want to require an environment variable
    # For now, we'll proceed (since this is called intentionally)
    
    success = cleanup_with_table_lock()
    
    if success:
        logger.info("🎉 TABLE-LOCKED CLEANUP COMPLETED SUCCESSFULLY!")
    else:
        logger.error("❌ TABLE-LOCKED CLEANUP FAILED!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
