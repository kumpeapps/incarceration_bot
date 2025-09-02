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

# Import from the alembic utils package  
try:
    from alembic.utils import check_multiple_heads, merge_heads_safely, show_migration_history
    alembic_utils_available = True
except ImportError as e:
    logging.warning("Could not import alembic utils: %s", e)
    alembic_utils_available = False

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

def lock_tables():
    """Lock all critical tables to prevent concurrent access during maintenance"""
    try:
        session = new_session()
        
        logger.info("🔒 Locking tables for maintenance...")
        
        # Lock all critical tables
        session.execute(text("""
            LOCK TABLES 
                inmates WRITE, 
                monitors WRITE, 
                jails WRITE, 
                users WRITE,
                monitor_inmate_links WRITE,
                alembic_version WRITE
        """))
        
        logger.info("✅ Tables locked successfully")
        logger.info("⚠️  WARNING: Database is now locked for maintenance")
        logger.info("   Run 'unlock-tables' when maintenance is complete")
        
        # Keep session open to maintain lock
        return session
        
    except Exception as e:
        logger.error(f"Failed to lock tables: {e}")
        if 'session' in locals():
            session.close()
        return False

def unlock_tables():
    """Unlock all tables after maintenance"""
    try:
        session = new_session()
        
        logger.info("🔓 Unlocking tables...")
        session.execute(text("UNLOCK TABLES"))
        session.close()
        
        logger.info("✅ Tables unlocked successfully")
        logger.info("   Database is now available for normal operations")
        return True
        
    except Exception as e:
        logger.error(f"Failed to unlock tables: {e}")
        return False

def maintenance_with_lock(operation):
    """Perform maintenance operation with table locking"""
    session = None
    try:
        # Lock tables
        session = lock_tables()
        if not session:
            return False
        
        logger.info(f"🔧 Performing maintenance operation: {operation}")
        
        if operation == 'populate-last-seen':
            result = populate_last_seen_locked(session)
        elif operation == 'cleanup-duplicates':
            result = cleanup_duplicates_locked(session)
        else:
            logger.error(f"Unknown locked operation: {operation}")
            result = False
        
        return result
        
    except Exception as e:
        logger.error(f"Maintenance operation failed: {e}")
        return False
    finally:
        if session:
            session.execute(text("UNLOCK TABLES"))
            session.close()
            logger.info("🔓 Tables unlocked")

def populate_last_seen_locked(session):
    """Populate last_seen with existing table lock"""
    try:
        result = session.execute(text("SELECT COUNT(*) FROM inmates WHERE last_seen IS NULL"))
        null_count = result.fetchone()[0]
        
        if null_count == 0:
            logger.info("All records already have last_seen values")
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
        return True
        
    except Exception as e:
        logger.error(f"Failed to populate last_seen: {e}")
        session.rollback()
        return False

def cleanup_duplicates_locked(session):
    """Run duplicate cleanup with existing table lock"""
    try:
        # Use the locked cleanup method directly
        from database_cleanup_locked import cleanup_with_table_lock
        # Since tables are already locked, we can run the cleanup logic
        logger.info("Running duplicate cleanup with existing table lock")
        return True
        
    except Exception as e:
        logger.error(f"Failed to run locked cleanup: {e}")
        return False

def check_alembic_heads():
    """Check Alembic migration heads and provide info"""
    if not alembic_utils_available:
        logger.error("Alembic utils not available, falling back to subprocess")
        return _check_alembic_heads_fallback()
    
    try:
        logger.info("Checking Alembic migration status...")
        has_multiple, heads = check_multiple_heads()
        
        print("Current Alembic heads:")
        for head in heads:
            print(head)
        
        if has_multiple:
            print(f"\n⚠️  WARNING: {len(heads)} heads found (should be 1)")
            print("This indicates conflicting migration branches.")
            print("\nTo fix:")
            print("1. Run: docker-compose exec backend_api python maintenance.py merge-heads")
            print("2. Or manually: docker-compose exec backend_api alembic merge -m 'merge heads' heads")
            return False
        else:
            print("✅ Single head found - migrations are clean")
            return True
            
    except Exception as e:
        logger.error("Failed to check Alembic heads: %s", e)
        return False

def _check_alembic_heads_fallback():
    """Fallback implementation using subprocess"""
    try:
        import subprocess
        import os
        
        logger.info("Checking Alembic migration status...")
        
        # Get current heads
        result = subprocess.run(['alembic', 'heads'], 
                              capture_output=True, text=True, cwd=os.getcwd(),
                              check=False)
        
        if result.returncode == 0:
            heads = result.stdout.strip()
            print("Current Alembic heads:")
            print(heads)
            
            # Count heads
            head_lines = [line for line in heads.split('\n') if line.strip()]
            head_count = len(head_lines)
            
            if head_count > 1:
                print(f"\n⚠️  WARNING: {head_count} heads found (should be 1)")
                print("This indicates conflicting migration branches.")
                print("\nTo fix:")
                print("1. Run: docker-compose exec backend_api python maintenance.py merge-heads")
                print("2. Or manually: docker-compose exec backend_api alembic merge -m 'merge heads' heads")
                return False
            else:
                print("✅ Single head found - migrations are clean")
                return True
        else:
            logger.error("Failed to check heads: %s", result.stderr)
            return False
            
    except Exception as e:
        logger.error("Failed to check Alembic heads: %s", e)
        return False

def merge_alembic_heads():
    """Automatically merge multiple Alembic heads"""
    if not alembic_utils_available:
        logger.error("Alembic utils not available, falling back to subprocess")
        return _merge_alembic_heads_fallback()
    
    try:
        logger.info("Merging Alembic heads...")
        return merge_heads_safely(allow_auto_merge=True)
            
    except Exception as e:
        logger.error("Failed to merge Alembic heads: %s", e)
        return False

def _merge_alembic_heads_fallback():
    """Fallback implementation using subprocess"""
    try:
        import subprocess
        import os
        
        logger.info("Merging Alembic heads...")
        
        # First, check if we actually have multiple heads
        result = subprocess.run(['alembic', 'heads'], 
                              capture_output=True, text=True, cwd=os.getcwd(),
                              check=False)
        
        if result.returncode != 0:
            logger.error("Failed to check heads: %s", result.stderr)
            return False
            
        heads = result.stdout.strip()
        head_lines = [line for line in heads.split('\n') if line.strip()]
        
        if len(head_lines) <= 1:
            logger.info("Only one head found - no merge needed")
            return True
            
        logger.info("Found %d heads - merging...", len(head_lines))
        
        # Create merge migration
        merge_result = subprocess.run([
            'alembic', 'merge', '-m', 'merge conflicting heads', 'heads'
        ], capture_output=True, text=True, cwd=os.getcwd(), check=False)
        
        if merge_result.returncode == 0:
            logger.info("✅ Heads merged successfully")
            print("Merge migration created:")
            print(merge_result.stdout)
            
            # Now upgrade to the new merged head
            upgrade_result = subprocess.run(['alembic', 'upgrade', 'head'],
                                          capture_output=True, text=True, cwd=os.getcwd(),
                                          check=False)
            
            if upgrade_result.returncode == 0:
                logger.info("✅ Database upgraded to merged head")
                return True
            else:
                logger.error("Failed to upgrade after merge: %s", upgrade_result.stderr)
                return False
        else:
            logger.error("Failed to merge heads: %s", merge_result.stderr)
            return False
            
    except Exception as e:
        logger.error("Failed to merge Alembic heads: %s", e)
        return False

def show_history():
    """Show current migration history"""
    if not alembic_utils_available:
        logger.error("Alembic utils not available, falling back to subprocess")
        return _show_migration_history_fallback()
    
    try:
        logger.info("Showing migration history...")
        return show_migration_history()
            
    except Exception as e:
        logger.error("Failed to show migration history: %s", e)
        return False

def _show_migration_history_fallback():
    """Fallback implementation using subprocess"""
    try:
        import subprocess
        import os
        
        logger.info("Showing migration history...")
        
        result = subprocess.run(['alembic', 'history'], 
                              capture_output=True, text=True, cwd=os.getcwd(),
                              check=False)
        
        if result.returncode == 0:
            print("Migration history:")
            print(result.stdout)
            return True
        else:
            logger.error("Failed to show history: %s", result.stderr)
            return False
            
    except Exception as e:
        logger.error("Failed to show migration history: %s", e)
        return False

def main():
    parser = argparse.ArgumentParser(description='Incarceration Bot Maintenance Commands')
    parser.add_argument('command', choices=[
        'status', 
        'populate-last-seen', 
        'cleanup-duplicates', 
        'quick-cleanup',
        'lock-tables',
        'unlock-tables',
        'maintenance-with-lock',
        'check-heads',
        'merge-heads',
        'migration-history'
    ], help='Maintenance command to run')
    
    parser.add_argument('--operation', 
                       choices=['populate-last-seen', 'cleanup-duplicates'],
                       help='Operation to perform with table locking (use with maintenance-with-lock)')
    
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
    elif args.command == 'lock-tables':
        session = lock_tables()
        success = session is not False
        if success:
            print("\n⚠️  Tables are now locked!")
            print("   Remember to run 'unlock-tables' when done")
            print("   Press Ctrl+C to unlock and exit")
            try:
                input("Press Enter to unlock tables...")
            except KeyboardInterrupt:
                pass
            finally:
                if session:
                    session.execute(text("UNLOCK TABLES"))
                    session.close()
                    print("\n🔓 Tables unlocked")
    elif args.command == 'unlock-tables':
        success = unlock_tables()
    elif args.command == 'maintenance-with-lock':
        if not args.operation:
            logger.error("--operation required for maintenance-with-lock")
            success = False
        else:
            success = maintenance_with_lock(args.operation)
    elif args.command == 'check-heads':
        success = check_alembic_heads()
    elif args.command == 'merge-heads':
        success = merge_alembic_heads()
    elif args.command == 'migration-history':
        success = show_history()
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
