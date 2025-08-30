#!/usr/bin/env python3
"""
Database Cleanup Script for Incarceration Bot
Removes duplicate records without managing Docker services
Run this while services are manually stopped
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
        logging.FileHandler('maintenance_cleanup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def analyze_duplicates():
    """Analyze the current duplicate situation"""
    logger.info("Analyzing duplicate records...")
    
    try:
        session = new_session()
        
        # Get total record count
        result = session.execute(text("SELECT COUNT(*) FROM inmates"))
        total_records = result.fetchone()[0]
        logger.info(f"Total records in database: {total_records:,}")
        
        # Get unique individuals count (using preferred constraint)
        result = session.execute(text("""
            SELECT COUNT(DISTINCT CONCAT(name, '|', COALESCE(race,''), '|', COALESCE(dob,''), '|', 
                                       COALESCE(sex,''), '|', COALESCE(arrest_date,''), '|', jail_id)) 
            FROM inmates
        """))
        unique_individuals = result.fetchone()[0]
        logger.info(f"Unique individuals (preferred constraint): {unique_individuals:,}")
        
        duplicates_to_remove = total_records - unique_individuals
        logger.info(f"Duplicate records to be removed: {duplicates_to_remove:,}")
        
        # Show some examples
        logger.info("Sample duplicate groups:")
        result = session.execute(text("""
            SELECT name, COUNT(*) as count 
            FROM inmates 
            GROUP BY name, race, dob, sex, arrest_date, jail_id 
            HAVING COUNT(*) > 1 
            ORDER BY count DESC 
            LIMIT 5
        """))
        
        for row in result:
            logger.info(f"  {row[0]}: {row[1]} duplicates")
            
        session.close()
        return {
            'total_records': total_records,
            'unique_individuals': unique_individuals,
            'duplicates_to_remove': duplicates_to_remove
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze duplicates: {e}")
        if 'session' in locals():
            session.close()
        return None

def cleanup_duplicates_batch(batch_size=5000):
    """Remove duplicate records in batches, keeping the most recent"""
    logger.info(f"Starting batch duplicate cleanup (batch size: {batch_size:,})...")
    
    try:
        session = new_session()
        
        # Set optimal transaction settings for large operations
        logger.info("Configuring transaction settings for cleanup...")
        session.execute(text("SET SESSION innodb_lock_wait_timeout = 120"))  # 2 minutes
        session.execute(text("SET SESSION tx_isolation = 'READ-COMMITTED'"))  # MariaDB syntax
        session.execute(text("SET SESSION autocommit = 0"))  # Explicit transaction control
        
        # Create a temporary table to identify records to keep (using correct column name)
        logger.info("Creating temporary table for cleanup...")
        session.execute(text("""
            CREATE TEMPORARY TABLE inmates_to_keep AS
            SELECT MAX(idinmates) as keep_id
            FROM inmates 
            GROUP BY name, race, dob, sex, arrest_date, jail_id
        """))
        session.commit()
        
        # Get count of records to delete
        result = session.execute(text("""
            SELECT COUNT(*) FROM inmates 
            WHERE idinmates NOT IN (SELECT keep_id FROM inmates_to_keep)
        """))
        total_to_delete = result.fetchone()[0]
        logger.info(f"Total records to delete: {total_to_delete:,}")
        
        if total_to_delete == 0:
            logger.info("No duplicates found to delete!")
            session.close()
            return 0
        
        # Delete in batches with proper transaction boundaries
        deleted_total = 0
        batch_num = 1
        start_time = time.time()
        
        while True:
            batch_start = time.time()
            logger.info(f"Processing batch {batch_num} (batch size: {batch_size:,})...")
            
            try:
                # Start explicit transaction for this batch
                session.execute(text("START TRANSACTION"))
                
                # Delete a batch - using MariaDB compatible syntax
                result = session.execute(text(f"""
                    DELETE FROM inmates 
                    WHERE idinmates NOT IN (SELECT keep_id FROM inmates_to_keep)
                    AND idinmates IN (
                        SELECT id FROM (
                            SELECT idinmates as id FROM inmates 
                            WHERE idinmates NOT IN (SELECT keep_id FROM inmates_to_keep)
                            ORDER BY idinmates 
                            LIMIT {batch_size}
                        ) as batch_ids
                    )
                """))
                
                deleted_count = result.rowcount
                
                if deleted_count == 0:
                    session.rollback()
                    break
                
                # Commit this batch
                session.commit()
                deleted_total += deleted_count
                
                batch_time = time.time() - batch_start
                total_time = time.time() - start_time
                avg_time_per_batch = total_time / batch_num
                
                logger.info(f"Batch {batch_num}: Deleted {deleted_count:,} records in {batch_time:.1f}s")
                logger.info(f"Progress: {deleted_total:,} / {total_to_delete:,} ({deleted_total/total_to_delete*100:.1f}%)")
                
                if total_to_delete > deleted_total:
                    remaining_batches = (total_to_delete - deleted_total + batch_size - 1) // batch_size
                    estimated_remaining_time = remaining_batches * avg_time_per_batch
                    logger.info(f"Estimated time remaining: {estimated_remaining_time/60:.1f} minutes")
                
                # Adaptive pause based on batch size and performance
                pause_time = min(1.0, batch_time * 0.1)  # Pause 10% of batch time, max 1 second
                time.sleep(pause_time)
                batch_num += 1
                
            except Exception as batch_error:
                logger.error(f"Error in batch {batch_num}: {batch_error}")
                session.rollback()
                # Continue with next batch rather than failing completely
                batch_num += 1
                time.sleep(2)  # Longer pause after error
                
            # Safety check - don't run forever
            if batch_num > 200:
                logger.warning("Reached maximum batch limit (200), stopping cleanup")
                break
        
        session.close()
        logger.info(f"✓ Duplicate cleanup completed! Removed {deleted_total:,} duplicate records")
        return deleted_total
        
    except Exception as e:
        logger.error(f"Failed during batch cleanup: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return 0

def verify_cleanup():
    """Verify the cleanup was successful"""
    logger.info("Verifying cleanup results...")
    
    try:
        session = new_session()
        
        # Check for remaining duplicates
        result = session.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT name, race, dob, sex, arrest_date, jail_id, COUNT(*) as count
                FROM inmates 
                GROUP BY name, race, dob, sex, arrest_date, jail_id 
                HAVING COUNT(*) > 1
            ) as duplicates
        """))
        remaining_duplicates = result.fetchone()[0]
        
        # Get final record count
        result = session.execute(text("SELECT COUNT(*) FROM inmates"))
        final_count = result.fetchone()[0]
        
        # Check our test case
        result = session.execute(text("""
            SELECT COUNT(*) FROM inmates WHERE name LIKE '%ABELINO-VICTORINO%'
        """))
        abelino_count = result.fetchone()[0]
        
        logger.info(f"Final record count: {final_count:,}")
        logger.info(f"Remaining duplicate groups: {remaining_duplicates}")
        logger.info(f"ABELINO-VICTORINO records remaining: {abelino_count}")
        
        session.close()
        
        if remaining_duplicates == 0:
            logger.info("✓ Cleanup successful - No duplicate groups remain!")
            return True
        else:
            logger.warning(f"⚠ {remaining_duplicates} duplicate groups still exist")
            return False
            
    except Exception as e:
        logger.error(f"Failed to verify cleanup: {e}")
        if 'session' in locals():
            session.close()
        return False

def main():
    """Main cleanup execution"""
    try:
        logger.info("=" * 60)
        logger.info("DATABASE CLEANUP STARTING")
        logger.info("=" * 60)
        
        # Step 1: Analyze current state
        analysis = analyze_duplicates()
        if not analysis:
            logger.error("Failed to analyze duplicates. Aborting.")
            return False
        
        # Step 2: Confirm execution
        logger.info("=" * 60)
        logger.info("CLEANUP ANALYSIS COMPLETE")
        logger.info(f"Will remove {analysis['duplicates_to_remove']:,} duplicate records")
        logger.info("=" * 60)
        
        if analysis['duplicates_to_remove'] == 0:
            logger.info("No duplicates to remove!")
            return True
        
        # Step 3: Cleanup duplicates
        deleted_count = cleanup_duplicates_batch()
        
        if deleted_count > 0:
            # Step 4: Verify cleanup
            if verify_cleanup():
                logger.info("✓ Database cleanup completed successfully!")
            else:
                logger.warning("⚠ Cleanup completed but verification found issues")
        else:
            logger.error("Cleanup failed")
            return False
        
        logger.info("🎉 DATABASE CLEANUP COMPLETED!")
        return True
        
    except KeyboardInterrupt:
        logger.info("Cleanup cancelled by user (Ctrl+C)")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during cleanup: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
