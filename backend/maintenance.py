#!/usr/bin/env python3
"""
Maintenance Commands for Incarceration Bot
Provides various maintenance operations that can be run from Docker
"""

import sys
import argparse
from datetime import datetime
from database_connect import new_session
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def status_check():
    """Check database status and provide overview"""
    try:
        session = new_session()
        
        # Basic counts
        result = session.execute(text("SELECT COUNT(*) FROM inmates"))
        total_inmates = result.fetchone()[0]
        
        result = session.execute(text("SELECT COUNT(*) FROM inmates WHERE last_seen IS NULL"))
        null_last_seen = result.fetchone()[0]
        
        result = session.execute(text("SELECT COUNT(*) FROM inmates WHERE DATE(last_seen) = CURDATE()"))
        today_updates = result.fetchone()[0]
        
        # Check for duplicates
        result = session.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT name, race, dob, sex, arrest_date, jail_id, COUNT(*) as count
                FROM inmates 
                GROUP BY name, race, dob, sex, arrest_date, jail_id 
                HAVING COUNT(*) > 1
            ) as duplicates
        """))
        duplicate_groups = result.fetchone()[0]
        
        # Sample recent records
        result = session.execute(text("""
            SELECT name, jail_id, last_seen 
            FROM inmates 
            WHERE last_seen IS NOT NULL 
            ORDER BY last_seen DESC 
            LIMIT 3
        """))
        recent_records = result.fetchall()
        
        session.close()
        
        print("=" * 50)
        print("INCARCERATION BOT DATABASE STATUS")
        print("=" * 50)
        print(f"Total inmate records: {total_inmates:,}")
        print(f"Records with NULL last_seen: {null_last_seen:,}")
        print(f"Records updated today: {today_updates:,}")
        print(f"Duplicate groups: {duplicate_groups:,}")
        
        if recent_records:
            print("\nRecent updates:")
            for record in recent_records:
                print(f"  {record[0]} | {record[1]} | {record[2]}")
        
        if null_last_seen > 0:
            print(f"\n⚠️  Warning: {null_last_seen:,} records need last_seen populated")
            print("   Run: docker-compose exec incarceration_bot python maintenance.py populate-last-seen")
        
        if duplicate_groups > 0:
            print(f"\n⚠️  Warning: {duplicate_groups:,} duplicate groups found")
            print("   Run: docker-compose exec incarceration_bot python maintenance.py cleanup-duplicates")
        
        return True
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return False

def populate_last_seen():
    """Populate missing last_seen dates"""
    try:
        session = new_session()
        
        result = session.execute(text("SELECT COUNT(*) FROM inmates WHERE last_seen IS NULL"))
        null_count = result.fetchone()[0]
        
        if null_count == 0:
            logger.info("All records already have last_seen values")
            session.close()
            return True
            
        logger.info(f"Updating {null_count:,} records with missing last_seen values")
        
        result = session.execute(text("""
            UPDATE inmates 
            SET last_seen = in_custody_date 
            WHERE last_seen IS NULL
        """))
        
        updated_count = result.rowcount
        session.commit()
        
        logger.info(f"✓ Updated {updated_count:,} records successfully")
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to populate last_seen: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

def cleanup_duplicates():
    """Run the full duplicate cleanup process"""
    try:
        from database_cleanup import main as cleanup_main
        return cleanup_main()
    except Exception as e:
        logger.error(f"Failed to run cleanup: {e}")
        return False

def quick_cleanup():
    """Quick duplicate cleanup with table lock (fastest)"""
    try:
        from database_cleanup_locked import main as cleanup_locked_main
        return cleanup_locked_main()
    except Exception as e:
        logger.error(f"Failed to run quick cleanup: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Incarceration Bot Maintenance Commands')
    parser.add_argument('command', choices=[
        'status', 'populate-last-seen', 'cleanup-duplicates', 'quick-cleanup'
    ], help='Maintenance command to run')
    
    args = parser.parse_args()
    
    print(f"Running maintenance command: {args.command}")
    print(f"Timestamp: {datetime.now()}")
    print("-" * 50)
    
    if args.command == 'status':
        success = status_check()
    elif args.command == 'populate-last-seen':
        success = populate_last_seen()
    elif args.command == 'cleanup-duplicates':
        success = cleanup_duplicates()
    elif args.command == 'quick-cleanup':
        success = quick_cleanup()
    else:
        logger.error(f"Unknown command: {args.command}")
        success = False
    
    if success:
        print("\n✅ Command completed successfully!")
    else:
        print("\n❌ Command failed!")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
