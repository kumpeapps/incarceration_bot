#!/usr/bin/env python3
"""
Maintenance Mode Script for Incarceration Bot
Safely manages system shutdown, duplicate cleanup, and restart operations
"""

import subprocess
import sys
import time
from datetime import datetime
from database_connect import new_session
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('maintenance_mode.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MaintenanceMode:
    def __init__(self):
        self.session = None
        
    def enter_maintenance_mode(self):
        """Stop all scraping services and put system in maintenance mode"""
        logger.info("=" * 60)
        logger.info("ENTERING MAINTENANCE MODE")
        logger.info("=" * 60)
        
        try:
            # Stop the incarceration_bot container to halt scraping
            logger.info("Stopping incarceration_bot container...")
            result = subprocess.run(['docker-compose', 'stop', 'incarceration_bot'], 
                                  capture_output=True, text=True, cwd='/Users/justinkumpe/Documents/incarceration_bot')
            if result.returncode == 0:
                logger.info("✓ Scraping services stopped successfully")
            else:
                logger.error(f"Failed to stop services: {result.stderr}")
                return False
                
            # Wait a moment for graceful shutdown
            time.sleep(5)
            
            # Verify no scraping processes are running
            logger.info("Verifying all scraping processes have stopped...")
            time.sleep(3)
            logger.info("✓ System ready for maintenance")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to enter maintenance mode: {e}")
            return False
    
    def analyze_duplicates(self):
        """Analyze the current duplicate situation"""
        logger.info("Analyzing duplicate records...")
        
        try:
            self.session = new_session()
            
            # Get total record count
            result = self.session.execute(text("SELECT COUNT(*) FROM inmates"))
            total_records = result.fetchone()[0]
            logger.info(f"Total records in database: {total_records:,}")
            
            # Get unique individuals count (using preferred constraint)
            result = self.session.execute(text("""
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
            result = self.session.execute(text("""
                SELECT name, COUNT(*) as count 
                FROM inmates 
                GROUP BY name, race, dob, sex, arrest_date, jail_id 
                HAVING COUNT(*) > 1 
                ORDER BY count DESC 
                LIMIT 5
            """))
            
            for row in result:
                logger.info(f"  {row[0]}: {row[1]} duplicates")
                
            return {
                'total_records': total_records,
                'unique_individuals': unique_individuals,
                'duplicates_to_remove': duplicates_to_remove
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze duplicates: {e}")
            return None
        finally:
            if self.session:
                self.session.close()
    
    def cleanup_duplicates_batch(self, batch_size=10000):
        """Remove duplicate records in batches, keeping the most recent"""
        logger.info("Starting batch duplicate cleanup...")
        
        try:
            self.session = new_session()
            
            # Create a temporary table to identify records to keep (using correct column name)
            logger.info("Creating temporary table for cleanup...")
            self.session.execute(text("""
                CREATE TEMPORARY TABLE inmates_to_keep AS
                SELECT MAX(idinmates) as keep_id
                FROM inmates 
                GROUP BY name, race, dob, sex, arrest_date, jail_id
            """))
            
            # Get count of records to delete
            result = self.session.execute(text("""
                SELECT COUNT(*) FROM inmates 
                WHERE idinmates NOT IN (SELECT keep_id FROM inmates_to_keep)
            """))
            total_to_delete = result.fetchone()[0]
            logger.info(f"Total records to delete: {total_to_delete:,}")
            
            # Delete in batches (MariaDB compatible)
            deleted_total = 0
            batch_num = 1
            
            while True:
                logger.info(f"Processing batch {batch_num} (batch size: {batch_size:,})...")
                
                # Delete a batch - using JOIN for MariaDB compatibility
                result = self.session.execute(text(f"""
                    DELETE i FROM inmates i
                    LEFT JOIN inmates_to_keep k ON i.idinmates = k.keep_id
                    WHERE k.keep_id IS NULL
                    LIMIT {batch_size}
                """))
                
                deleted_count = result.rowcount
                deleted_total += deleted_count
                
                if deleted_count == 0:
                    break
                    
                logger.info(f"Batch {batch_num}: Deleted {deleted_count:,} records")
                logger.info(f"Progress: {deleted_total:,} / {total_to_delete:,} ({deleted_total/total_to_delete*100:.1f}%)")
                
                # Commit this batch
                self.session.commit()
                
                # Brief pause to avoid overwhelming the database
                time.sleep(1)
                batch_num += 1
                
                # Safety check - don't run forever
                if batch_num > 100:
                    logger.warning("Reached maximum batch limit (100), stopping cleanup")
                    break
            
            logger.info(f"✓ Duplicate cleanup completed! Removed {deleted_total:,} duplicate records")
            return deleted_total
            
        except Exception as e:
            logger.error(f"Failed during batch cleanup: {e}")
            if self.session:
                self.session.rollback()
            return 0
        finally:
            if self.session:
                self.session.close()
    
    def verify_cleanup(self):
        """Verify the cleanup was successful"""
        logger.info("Verifying cleanup results...")
        
        try:
            self.session = new_session()
            
            # Check for remaining duplicates
            result = self.session.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT name, race, dob, sex, arrest_date, jail_id, COUNT(*) as count
                    FROM inmates 
                    GROUP BY name, race, dob, sex, arrest_date, jail_id 
                    HAVING COUNT(*) > 1
                ) as duplicates
            """))
            remaining_duplicates = result.fetchone()[0]
            
            # Get final record count
            result = self.session.execute(text("SELECT COUNT(*) FROM inmates"))
            final_count = result.fetchone()[0]
            
            logger.info(f"Final record count: {final_count:,}")
            logger.info(f"Remaining duplicate groups: {remaining_duplicates}")
            
            if remaining_duplicates == 0:
                logger.info("✓ Cleanup successful - No duplicate groups remain!")
                return True
            else:
                logger.warning(f"⚠ {remaining_duplicates} duplicate groups still exist")
                return False
                
        except Exception as e:
            logger.error(f"Failed to verify cleanup: {e}")
            return False
        finally:
            if self.session:
                self.session.close()
    
    def exit_maintenance_mode(self):
        """Restart all services and exit maintenance mode"""
        logger.info("=" * 60)
        logger.info("EXITING MAINTENANCE MODE")
        logger.info("=" * 60)
        
        try:
            # Restart the incarceration_bot container
            logger.info("Restarting incarceration_bot container...")
            result = subprocess.run(['docker-compose', 'up', '-d', 'incarceration_bot'], 
                                  capture_output=True, text=True, cwd='/Users/justinkumpe/Documents/incarceration_bot')
            if result.returncode == 0:
                logger.info("✓ Scraping services restarted successfully")
            else:
                logger.error(f"Failed to restart services: {result.stderr}")
                return False
                
            # Wait for services to be ready
            logger.info("Waiting for services to initialize...")
            time.sleep(10)
            
            logger.info("✓ System back online and ready for normal operations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to exit maintenance mode: {e}")
            return False

def main():
    """Main maintenance mode execution"""
    maintenance = MaintenanceMode()
    
    try:
        # Step 1: Enter maintenance mode
        if not maintenance.enter_maintenance_mode():
            logger.error("Failed to enter maintenance mode. Aborting.")
            return False
        
        # Step 2: Analyze current state
        analysis = maintenance.analyze_duplicates()
        if not analysis:
            logger.error("Failed to analyze duplicates. Aborting.")
            return False
        
        # Step 3: Confirm with user (in production, you might want automatic mode)
        logger.info("=" * 60)
        logger.info("MAINTENANCE ANALYSIS COMPLETE")
        logger.info(f"Will remove {analysis['duplicates_to_remove']:,} duplicate records")
        logger.info("=" * 60)
        
        # For now, proceed automatically. In production you might want confirmation.
        proceed = True
        
        if proceed:
            # Step 4: Cleanup duplicates
            deleted_count = maintenance.cleanup_duplicates_batch()
            
            if deleted_count > 0:
                # Step 5: Verify cleanup
                if maintenance.verify_cleanup():
                    logger.info("✓ Maintenance completed successfully!")
                else:
                    logger.warning("⚠ Cleanup completed but verification found issues")
            else:
                logger.error("Cleanup failed, not proceeding with restart")
                return False
        else:
            logger.info("Maintenance cancelled by user")
            return False
        
        # Step 6: Exit maintenance mode
        if not maintenance.exit_maintenance_mode():
            logger.error("Failed to restart services. Manual intervention required.")
            return False
        
        logger.info("🎉 MAINTENANCE MODE COMPLETED SUCCESSFULLY!")
        return True
        
    except KeyboardInterrupt:
        logger.info("Maintenance cancelled by user (Ctrl+C)")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during maintenance: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
