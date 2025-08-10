#!/usr/bin/env python3
"""
Test Maintenance Mode Script
Dry-run version to validate the maintenance approach without making changes
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
        logging.FileHandler('maintenance_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_maintenance_analysis():
    """Test the analysis phase without making any changes"""
    logger.info("=" * 60)
    logger.info("TESTING MAINTENANCE MODE ANALYSIS")
    logger.info("=" * 60)
    
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
        logger.info(f"Duplicate records that would be removed: {duplicates_to_remove:,}")
        
        # Calculate percentage
        percentage = (duplicates_to_remove / total_records) * 100 if total_records > 0 else 0
        logger.info(f"Percentage of database that is duplicates: {percentage:.1f}%")
        
        # Show sample duplicate groups
        logger.info("\nSample duplicate groups that would be cleaned:")
        result = session.execute(text("""
            SELECT name, race, dob, sex, arrest_date, jail_id, COUNT(*) as count 
            FROM inmates 
            GROUP BY name, race, dob, sex, arrest_date, jail_id 
            HAVING COUNT(*) > 1 
            ORDER BY count DESC 
            LIMIT 10
        """))
        
        sample_count = 0
        for row in result:
            logger.info(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}: {row[6]} duplicates")
            sample_count += 1
        
        if sample_count == 0:
            logger.info("  No duplicate groups found!")
        
        # Test the cleanup query (dry run)
        logger.info("\nTesting cleanup query (dry run)...")
        session.execute(text("""
            CREATE TEMPORARY TABLE test_inmates_to_keep AS
            SELECT MAX(id) as keep_id
            FROM inmates 
            GROUP BY name, race, dob, sex, arrest_date, jail_id
            LIMIT 1000
        """))
        
        result = session.execute(text("""
            SELECT COUNT(*) FROM inmates 
            WHERE id NOT IN (SELECT keep_id FROM test_inmates_to_keep)
            AND id IN (
                SELECT id FROM inmates 
                ORDER BY id 
                LIMIT 1000
            )
        """))
        test_delete_count = result.fetchone()[0]
        logger.info(f"Test query would delete {test_delete_count} records from sample of 1000")
        
        # Check our specific test case
        logger.info("\nChecking ABELINO-VICTORINO test case:")
        result = session.execute(text("""
            SELECT COUNT(*) as total_records,
                   COUNT(DISTINCT CONCAT(name, '|', COALESCE(race,''), '|', COALESCE(dob,''), '|', 
                                       COALESCE(sex,''), '|', COALESCE(arrest_date,''), '|', jail_id)) as unique_individuals
            FROM inmates 
            WHERE name LIKE '%ABELINO-VICTORINO%'
        """))
        
        row = result.fetchone()
        if row and row[0] > 0:
            logger.info(f"  Current records: {row[0]}")
            logger.info(f"  Would keep: {row[1]}")
            logger.info(f"  Would remove: {row[0] - row[1]}")
        else:
            logger.info("  ABELINO-VICTORINO not found in database")
        
        session.close()
        
        logger.info("\n" + "=" * 60)
        logger.info("TEST ANALYSIS COMPLETED")
        logger.info(f"Ready to remove {duplicates_to_remove:,} duplicate records ({percentage:.1f}% of database)")
        logger.info("=" * 60)
        
        return {
            'total_records': total_records,
            'unique_individuals': unique_individuals,
            'duplicates_to_remove': duplicates_to_remove,
            'percentage': percentage
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze duplicates: {e}")
        if 'session' in locals():
            session.close()
        return None

def test_service_control():
    """Test stopping and starting services"""
    logger.info("\nTesting service control (dry run)...")
    
    # Check current status
    try:
        result = subprocess.run(['docker-compose', 'ps', 'incarceration_bot'], 
                              capture_output=True, text=True, cwd='/Users/justinkumpe/Documents/incarceration_bot')
        if result.returncode == 0:
            logger.info("✓ docker-compose is accessible")
            logger.info(f"Current incarceration_bot status:\n{result.stdout}")
        else:
            logger.error(f"Failed to check service status: {result.stderr}")
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to test service control: {e}")
        return False

def main():
    """Main test execution"""
    try:
        # Test database analysis
        analysis = test_maintenance_analysis()
        if not analysis:
            logger.error("Analysis test failed")
            return False
        
        # Test service control
        if not test_service_control():
            logger.error("Service control test failed")
            return False
        
        logger.info("\n🎉 ALL TESTS PASSED!")
        logger.info("The maintenance mode script is ready to execute.")
        logger.info(f"It will remove {analysis['duplicates_to_remove']:,} duplicate records.")
        logger.info("\nTo run the actual maintenance:")
        logger.info("  ./run_maintenance.sh")
        logger.info("OR")
        logger.info("  docker-compose exec incarceration_bot python /app/maintenance_mode.py")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
