"""
Optimized Process Module for Reduced Database Writes

This replaces the standard process.py with optimizations to reduce MariaDB binlog bloat:
1. Batch database operations
2. Only update timestamps when necessary
3. Reduce commit frequency
4. Optimize upsert operations
"""

from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.Inmate import Inmate
from models.Monitor import Monitor
from models.Jail import Jail
from helpers.database_optimizer import DatabaseOptimizer


def process_inmates_optimized(
    inmates: list[Inmate],
    jail: Jail,
    session: Session,
    batch_size: int = 100
):
    """
    Optimized version of process_inmates that reduces database writes.
    
    Args:
        inmates: List of scraped inmate objects
        jail: Jail object
        session: SQLAlchemy session
        batch_size: Number of records to process in batches
    """
    logger.info(f"Processing {len(inmates)} inmates for {jail.jail_name} (optimized)")
    
    if not inmates:
        logger.warning("No inmates to process")
        return
    
    # Prepare data for batch operations
    inmate_data_list = []
    monitor_updates = []
    
    # First pass: collect all data and monitor updates
    for inmate in inmates:
        try:
            # Add current datetime for last_seen
            inmate.last_seen = datetime.now()
            
            # Convert to dict for batch processing
            inmate_dict = inmate.to_dict()
            inmate_data_list.append(inmate_dict)
            
            # Check for monitors (collect updates for batch processing)
            monitor_updates.extend(_collect_monitor_updates(session, inmate, jail))
            
        except Exception as error:
            logger.error(f"Error preparing inmate {getattr(inmate, 'name', 'Unknown')}: {error}")
            continue
    
    # Batch process inmates - this is the major optimization
    if inmate_data_list:
        try:
            DatabaseOptimizer.batch_upsert_inmates(session, inmate_data_list, batch_size)
            logger.success(f"Batch processed {len(inmate_data_list)} inmates")
        except Exception as error:
            logger.error(f"Batch processing failed, falling back to individual inserts: {error}")
            _fallback_individual_processing(session, inmates, jail)
    
    # Batch process monitor updates
    if monitor_updates:
        try:
            DatabaseOptimizer.optimize_monitor_updates(session, monitor_updates)
            logger.success(f"Batch updated {len(monitor_updates)} monitors")
        except Exception as error:
            logger.error(f"Failed to batch update monitors: {error}")
    
    # Check for released inmates (single operation at the end)
    try:
        check_for_released_inmates_optimized(session, inmates, jail)
        logger.debug("Checked for released inmates")
    except Exception as error:
        logger.error(f"Failed to check for released inmates: {error}")
        session.rollback()
    
    # Update jail's last scrape date (single update)
    try:
        jail.update_last_scrape_date()
        session.commit()
        logger.debug("Updated jail last scrape date")
    except Exception as error:
        logger.error(f"Failed to update jail last scrape date: {error}")
        session.rollback()


def _collect_monitor_updates(session: Session, inmate: Inmate, jail: Jail) -> list[tuple]:
    """
    Collect monitor updates for batch processing instead of individual commits.
    
    Returns:
        List of (monitor_id, last_seen_incarcerated) tuples
    """
    updates = []
    
    try:
        # Get exact matches
        exact_matches = session.query(Monitor).filter(
            Monitor.name.ilike(f"%{inmate.name}%"),
            Monitor.jail.ilike(f"%{jail.jail_name}%")
        ).all()
        
        for monitor in exact_matches:
            # Add to batch update list instead of immediate update
            updates.append((monitor.id, datetime.now()))
            
            # Check if this is a new incarceration (notification logic remains the same)
            if monitor.last_seen_incarcerated is None:
                try:
                    monitor.send_message(inmate)
                    logger.info(f"Sent notification for new incarceration: {monitor.name}")
                except Exception as error:
                    logger.error(f"Failed to send notification for {monitor.name}: {error}")
        
        # Check for partial matches if no exact matches
        if not exact_matches:
            # Split name and check for partial matches
            name_parts = str(inmate.name).split()
            if len(name_parts) >= 2:
                first_name, last_name = name_parts[0], name_parts[-1]
                
                partial_matches = session.query(Monitor).filter(
                    Monitor.name.ilike(f"%{first_name}%"),
                    Monitor.name.ilike(f"%{last_name}%"),
                    Monitor.jail.ilike(f"%{jail.jail_name}%")
                ).all()
                
                for monitor in partial_matches:
                    # Add to batch update list
                    updates.append((monitor.id, datetime.now()))
                    
                    # Check if this is a new incarceration
                    if monitor.last_seen_incarcerated is None:
                        try:
                            monitor.send_message(inmate)
                            logger.info(f"Sent notification for partial match: {monitor.name}")
                        except Exception as error:
                            logger.error(f"Failed to send notification for {monitor.name}: {error}")
        
    except Exception as error:
        logger.error(f"Error collecting monitor updates for {inmate.name}: {error}")
    
    return updates


def _fallback_individual_processing(session: Session, inmates: list[Inmate], jail: Jail):
    """
    Fallback to individual processing if batch operations fail.
    """
    logger.warning("Using fallback individual processing")
    
    for inmate in inmates:
        try:
            # Use optimized upsert even for individual records
            inmate.last_seen = datetime.now()
            DatabaseOptimizer.optimized_upsert_inmate(session, inmate.to_dict(), auto_commit=False)
        except Exception as error:
            logger.error(f"Failed to process inmate {getattr(inmate, 'name', 'Unknown')}: {error}")
    
    try:
        session.commit()
    except Exception as error:
        logger.error(f"Failed to commit individual processing: {error}")
        session.rollback()


def check_for_released_inmates_optimized(session: Session, current_inmates: list[Inmate], jail: Jail):
    """
    Optimized version of release checking that uses batch operations.
    """
    logger.debug(f"Checking for released inmates in {jail.jail_name}")
    
    # Get monitors to check (same logic as original)
    monitors_to_check = session.query(Monitor).filter(
        Monitor.jail == jail.jail_name,
        Monitor.last_seen_incarcerated.isnot(None),
        Monitor.release_date.is_(None)
    ).all()
    
    if not monitors_to_check:
        logger.debug(f"No monitors to check for releases in {jail.jail_name}")
        return
    
    logger.debug(f"Found {len(monitors_to_check)} monitors to check for releases")
    
    # Create set of current inmate names for fast lookup
    current_inmate_names = {str(inmate.name).strip().lower() for inmate in current_inmates}
    
    # Collect all release updates for batch processing
    release_updates = []
    notification_tasks = []
    
    for monitor in monitors_to_check:
        monitor_name = str(monitor.name).strip().lower()
        
        if monitor_name not in current_inmate_names:
            # Monitor not found - likely released
            release_date_str = datetime.now().strftime("%Y-%m-%d")
            logger.info(f"Monitor {monitor.name} (ID: {monitor.id}) appears released from {jail.jail_name}")
            
            # Collect for batch update
            release_updates.append((monitor.id, release_date_str))
            
            # Collect notification task
            notification_tasks.append((monitor, release_date_str, jail))
    
    # Batch update release dates if any
    if release_updates:
        try:
            # Use batch update for release dates
            from sqlalchemy import text
            
            params = {}
            when_clauses = []
            monitor_ids = []
            
            for i, (monitor_id, release_date) in enumerate(release_updates):
                when_clauses.append(f"WHEN id = :monitor_id_{i} THEN :release_date_{i}")
                params[f'monitor_id_{i}'] = monitor_id
                params[f'release_date_{i}'] = release_date
                monitor_ids.append(f":monitor_id_{i}")
            
            sql = text(f"""
                UPDATE monitors 
                SET release_date = CASE 
                    {' '.join(when_clauses)}
                    ELSE release_date
                END
                WHERE id IN ({', '.join(monitor_ids)})
            """)
            
            session.execute(sql, params)
            session.commit()
            
            logger.info(f"Batch updated {len(release_updates)} monitors as released")
            
        except Exception as error:
            logger.error(f"Failed to batch update release dates: {error}")
            session.rollback()
    
    # Send notifications (these still need to be individual due to message sending)
    for monitor, release_date_str, jail in notification_tasks:
        try:
            # Create dummy inmate for notification
            dummy_inmate = Inmate(
                name=monitor.name,
                race="Unknown",
                sex="Unknown",
                cell_block=None,
                arrest_date=monitor.arrest_date,
                held_for_agency=monitor.arresting_agency or "Unknown",
                mugshot=monitor.mugshot,
                dob="Unknown",
                hold_reasons=monitor.arrest_reason or "Unknown",
                is_juvenile=False,
                release_date=release_date_str,
                in_custody_date=monitor.arrest_date or datetime.now().date(),
                jail_id=jail.jail_id,
                hide_record=False,
            )
            
            monitor.send_message(dummy_inmate, released=True)
            logger.success(f"Sent release notification for {monitor.name}")
            
        except Exception as error:
            logger.error(f"Failed to send release notification for {monitor.name}: {error}")


# Compatibility function - can be used as drop-in replacement
def process_inmates(inmates: list[Inmate], jail: Jail, session: Session):
    """
    Drop-in replacement for the original process_inmates function.
    Uses optimized processing by default.
    """
    process_inmates_optimized(inmates, jail, session)
