#!/usr/bin/env python3
"""
Release Date Maintenance Script

This script processes release date updates for large jails that were deferred
during the main scraping process to avoid lock contention and timeouts.

Can be run as a separate background job or cron task.
"""

import os
import sys
import time
from datetime import date, datetime, timedelta
from loguru import logger

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from database_connect import new_session
from models.Inmate import Inmate
from models.Jail import Jail
from helpers.database_optimizer import DatabaseOptimizer


def process_deferred_release_dates(jail_id: str = None, batch_size: int = 3, delay_between_batches: float = 2.0):
    """
    Process release date updates that were deferred during main scraping.
    
    Args:
        jail_id: Specific jail to process, or None for all jails
        batch_size: Very small batch size to avoid lock contention
        delay_between_batches: Seconds to wait between batches
    """
    session = new_session()
    
    try:
        # Configure session for background processing
        session.execute("SET SESSION transaction_isolation = 'READ-UNCOMMITTED'")
        session.execute("SET SESSION innodb_lock_wait_timeout = 10")
        
        # Get jails to process
        if jail_id:
            jails = session.query(Jail).filter(Jail.jail_id == jail_id).all()
        else:
            jails = session.query(Jail).filter(Jail.enabled == True).all()
        
        logger.info(f"Processing deferred release dates for {len(jails)} jails")
        
        for jail in jails:
            logger.info(f"Processing release dates for {jail.jail_name}")
            
            # Get inmates that need release date updates
            today = date.today()
            yesterday = today - timedelta(days=1)
            yesterday_start = datetime.combine(yesterday, datetime.min.time())
            
            inmates_to_update = (
                session.query(Inmate)
                .filter(
                    Inmate.jail_id == jail.jail_id,
                    Inmate.release_date.in_(["", None]),
                    Inmate.last_seen < yesterday_start  # Not seen since yesterday
                )
                .all()
            )
            
            if not inmates_to_update:
                logger.debug(f"No deferred release dates to process for {jail.jail_name}")
                continue
            
            logger.info(f"Found {len(inmates_to_update)} inmates needing release date updates in {jail.jail_name}")
            
            # Get current inmates for this jail (from today's scrape)
            current_inmates = (
                session.query(Inmate)
                .filter(
                    Inmate.jail_id == jail.jail_id,
                    Inmate.last_seen >= datetime.combine(today, datetime.min.time())
                )
                .all()
            )
            
            # Create lookup set of current inmates
            current_identifiers = {
                (str(inmate.name).strip().lower(), inmate.arrest_date) 
                for inmate in current_inmates
            }
            
            # Collect release date updates
            release_updates = []
            for inmate in inmates_to_update:
                inmate_identifier = (str(inmate.name).strip().lower(), inmate.arrest_date)
                
                if inmate_identifier not in current_identifiers:
                    # This inmate is no longer in current roster - set release date
                    if inmate.last_seen:
                        release_date_str = inmate.last_seen.date().isoformat()
                    else:
                        release_date_str = yesterday.isoformat()
                    
                    release_updates.append((inmate.id, release_date_str))
            
            # Process updates with background-friendly method
            if release_updates:
                updated_count = DatabaseOptimizer.batch_update_release_dates_background(
                    session, release_updates, batch_size=batch_size
                )
                logger.info(f"Updated {updated_count} release dates for {jail.jail_name}")
                
                # Wait between jails to be extra gentle
                if delay_between_batches > 0:
                    time.sleep(delay_between_batches)
            else:
                logger.debug(f"No release date updates needed for {jail.jail_name}")
        
        logger.info("Completed deferred release date processing")
        
    except Exception as e:
        logger.error(f"Error in deferred release date processing: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process deferred release date updates")
    parser.add_argument("--jail-id", help="Specific jail ID to process")
    parser.add_argument("--batch-size", type=int, default=3, help="Batch size for updates")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between batches (seconds)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.add(sys.stdout, level="DEBUG")
    else:
        logger.add(sys.stdout, level="INFO")
    
    process_deferred_release_dates(
        jail_id=args.jail_id,
        batch_size=args.batch_size,
        delay_between_batches=args.delay
    )
