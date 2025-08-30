"""Optimized process scraped data"""

from datetime import datetime, date
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from loguru import logger
from models.Jail import Jail
from models.Inmate import Inmate
from models.Monitor import Monitor
from helpers.insert_ignore import upsert_inmate
from helpers.database_optimizer import DatabaseOptimizer


def process_scrape_data_optimized(session: Session, inmates: List[Inmate], jail: Jail):
    """
    Optimized version of process scraped inmate data and update the database.

    Optimizations:
    - Pre-load all monitors once
    - Create name lookup dictionaries for faster matching
    - Batch database operations
    - Reduce session commits

    Args:
        session (Session): SQLAlchemy session for database operations.
        inmates (List[Inmate]): List of Inmate objects containing scraped data.
        jail (Jail): Jail object containing jail details.

    Returns:
        None
    """
    logger.info(f"Processing {jail.jail_name} (optimized)")

    # Pre-load all monitors once
    monitors = session.query(Monitor).all()

    # Create lookup dictionaries for faster matching
    monitor_by_exact_name: Dict[str, Monitor] = {}
    monitor_partial_matches: List[Monitor] = []

    for monitor in monitors:
        monitor_name = str(monitor.name)
        monitor_by_exact_name[monitor_name] = monitor
        monitor_partial_matches.append(monitor)

    # Process each inmate
    monitors_to_update = []
    new_monitors = []
    inmates_to_insert = []

    for inmate in inmates:
        inmate_processed = False

        # Check for exact name match first (fastest)
        inmate_name = str(inmate.name)
        if inmate_name in monitor_by_exact_name:
            monitor = monitor_by_exact_name[inmate_name]

            # Always update last_seen_incarcerated when monitor is found
            monitor.last_seen_incarcerated = datetime.now()  # type: ignore

            # Check for new arrest date
            if monitor.arrest_date != inmate.arrest_date:
                logger.trace(f"New arrest date for {monitor.name}")
                monitor.arrest_date = inmate.arrest_date
                monitor.release_date = None # type: ignore
                monitor.send_message(inmate)
                inmate_processed = True
            elif (
                inmate.release_date
                and monitor.release_date != inmate.release_date
                and inmate.release_date != ""
            ):
                logger.info(f"New release date for {monitor.name}")
                monitor.release_date = inmate.release_date
                monitor.send_message(inmate, released=True)

            # Always add to update list since we updated last_seen_incarcerated
            monitors_to_update.append(monitor)

        # If no exact match, check for partial matches
        if not inmate_processed:
            for monitor in monitor_partial_matches:
                if monitor.name in inmate.name and monitor.name != inmate.name:
                    logger.info(f"Matched {monitor.name} to {inmate.name}")

                    # Check if there's already an exact match monitor
                    if inmate_name in monitor_by_exact_name:
                        logger.info(
                            f"Found full name match for {inmate.name}, Skipping partial match"
                        )
                        continue

                    if monitor.arrest_date != inmate.arrest_date:
                        logger.trace(
                            f"New arrest date for partial match {monitor.name}"
                        )
                        logger.success(f"Creating new monitor for {inmate.name}")

                        new_monitor = Monitor(  # pylint: disable=unexpected-keyword-arg
                            name=inmate.name,
                            arrest_date=inmate.arrest_date,
                            release_date=None,
                            jail=jail.jail_name,
                            mugshot=inmate.mugshot,
                            enable_notifications=monitor.enable_notifications,
                            notify_method=monitor.notify_method,
                            notify_address=monitor.notify_address,
                            last_seen_incarcerated=datetime.now(),
                        )
                        new_monitors.append(new_monitor)
                        monitor_by_exact_name[inmate_name] = (
                            new_monitor  # Add to lookup for future inmates
                        )
                        monitor.send_message(inmate)
                        break

        # Always try to insert the inmate record with updated last_seen
        inmate.last_seen = datetime.now()
        inmates_to_insert.append(inmate)

    # Batch database operations - handle upserts for inmates
    try:
        # Add new monitors
        if new_monitors:
            logger.info(f"Adding {len(new_monitors)} new monitors")
            for monitor in new_monitors:
                session.add(monitor)

        # Process inmates with batch upsert for performance
        if inmates_to_insert:
            logger.info(f"Processing {len(inmates_to_insert)} inmates with optimized batch upsert")
            
            # Convert inmates to dictionaries for batch processing
            inmates_data = [inmate.to_dict() for inmate in inmates_to_insert]
            
            # Use the optimized batch upsert method
            try:
                DatabaseOptimizer.batch_upsert_inmates(
                    session=session, 
                    inmates_data=inmates_data, 
                    batch_size=50  # Smaller batch size for timeout prevention
                )
                logger.info("Successfully completed optimized batch upsert")
            except Exception as batch_error:
                logger.error(f"Batch upsert failed, falling back to individual upserts: {batch_error}")
                
                # Fallback to individual processing in smaller batches
                batch_size = 50
                total_batches = (len(inmates_to_insert) + batch_size - 1) // batch_size
                
                for i in range(0, len(inmates_to_insert), batch_size):
                    batch = inmates_to_insert[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    
                    logger.info(f"Fallback batch {batch_num}/{total_batches} ({len(batch)} inmates)")
                    
                    for inmate in batch:
                        try:
                            upsert_inmate(session, inmate.to_dict())
                        except Exception as inmate_error:
                            logger.error(f"Failed to upsert inmate {inmate.name}: {inmate_error}")
                    
                    # Commit each batch
                    try:
                        session.commit()
                        logger.debug(f"Committed fallback batch {batch_num}/{total_batches}")
                    except Exception as commit_error:
                        logger.error(f"Failed to commit fallback batch {batch_num}: {commit_error}")
                        session.rollback()
                        raise

    except Exception as error:
        logger.error(f"Failed to process inmates: {error}")
        session.rollback()
        raise

    # Check for released inmates (those no longer in jail)
    try:
        check_for_released_inmates(session, inmates, jail)
        # Also check for released inmates in the main inmates table
        update_release_dates_for_missing_inmates(session, inmates, jail)
        session.commit()
        logger.debug("Checked for released inmates and updated release dates")
    except Exception as error:
        logger.error(f"Failed to check for released inmates: {error}")
        session.rollback()

    # Update jail's last scrape date
    try:
        jail.update_last_scrape_date()
        session.commit()
        logger.debug("Updated jail last scrape date")
    except Exception as error:
        logger.error(f"Failed to update jail last scrape date: {error}")
        session.rollback()


def check_for_released_inmates(
    session: Session, current_inmates: List[Inmate], jail: Jail
):
    """
    Check for monitors that were previously incarcerated but are no longer
    in the current batch of scraped inmates, indicating they may have been released.

    Args:
        session (Session): SQLAlchemy session for database operations.
        current_inmates (List[Inmate]): List of currently scraped inmates.
        jail (Jail): Jail object containing jail details.
    """
    logger.debug(f"Checking for released inmates in {jail.jail_name}")

    # Get all monitors for this jail that have been seen incarcerated
    # and don't already have a release date
    monitors_to_check = (
        session.query(Monitor)
        .filter(
            Monitor.jail == jail.jail_name,
            Monitor.last_seen_incarcerated.isnot(None),
            Monitor.release_date.is_(None),
        )
        .all()
    )

    if not monitors_to_check:
        logger.debug(f"No monitors to check for releases in {jail.jail_name}")
        return

    logger.debug(f"Found {len(monitors_to_check)} monitors to check for releases")

    # Create a set of current inmate names for fast lookup
    current_inmate_names = {
        str(inmate.name).strip().lower() for inmate in current_inmates
    }

    released_monitors = []

    for monitor in monitors_to_check:
        monitor_name = str(monitor.name).strip().lower()

        # Check if monitor is still in current inmates list
        if monitor_name not in current_inmate_names:
            # Monitor not found in current inmates - likely released
            logger.info(
                f"Monitor {monitor.name} appears to have been released from {jail.jail_name}"
            )

            # Prefer to use the last date the inmate was seen as the release date, if available
            last_seen_date = getattr(monitor, "last_seen_date", None)
            if last_seen_date:
                release_date_str = last_seen_date.strftime("%Y-%m-%d")
                logger.info(f"Setting release date for {monitor.name} to last seen date: '{release_date_str}'")
            else:
                release_date_str = datetime.now().strftime("%Y-%m-%d")
                logger.warning(
                    f"Release date for {monitor.name} is uncertain; using current date '{release_date_str}' as fallback"
                )
            monitor.release_date = release_date_str  # type: ignore
            logger.debug(f"Monitor.release_date is now: '{monitor.release_date}'")

            # Create a dummy inmate object for the release notification
            # We'll use the monitor's stored information
            dummy_inmate = Inmate(  # pylint: disable=unexpected-keyword-arg
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

            # Send release notification
            try:
                monitor.send_message(dummy_inmate, released=True)
                logger.success(f"Sent release notification for {monitor.name}")
            except Exception as error:
                logger.error(
                    f"Failed to send release notification for {monitor.name}: {error}"
                )

            released_monitors.append(monitor)

    if released_monitors:
        logger.info(
            f"Marked {len(released_monitors)} monitors as released from {jail.jail_name}"
        )
    else:
        logger.debug(f"No releases detected in {jail.jail_name}")


def update_release_dates_for_missing_inmates(
    session: Session, current_inmates: List[Inmate], jail: Jail
):
    """
    Update release_date for inmates who are no longer present in the current scrape
    and have a blank release_date, indicating they have been released.

    Args:
        session (Session): SQLAlchemy session for database operations.
        current_inmates (List[Inmate]): List of currently scraped inmates.
        jail (Jail): Jail object containing jail details.
    """
    logger.debug(f"Checking for inmates to update release dates in {jail.jail_name}")

    # Get all inmates for this jail that don't have a release date and last_seen is not today
    today = date.today()
    today_start_dt = datetime.combine(today, datetime.min.time())  # Start of today as datetime
    
    inmates_to_check = (
        session.query(Inmate)
        .filter(
            Inmate.jail_id == jail.jail_id,
            Inmate.release_date.in_(["", None]),  # Blank or null release date
            Inmate.last_seen < today_start_dt  # last_seen is before today
        )
        .all()
    )

    if not inmates_to_check:
        logger.debug(f"No inmates need release date updates in {jail.jail_name}")
        return

    logger.info(f"Found {len(inmates_to_check)} inmates to check for release date updates in {jail.jail_name}")

    # Create a set of current inmate identifiers (name + arrest_date) for fast lookup
    current_inmate_identifiers = {
        (str(inmate.name).strip().lower(), inmate.arrest_date) for inmate in current_inmates
    }
    
    logger.debug(f"Current scrape has {len(current_inmate_identifiers)} unique inmate records")
    logger.debug(f"Checking {len(inmates_to_check)} inmates with old last_seen dates")

    updated_count = 0

    for inmate in inmates_to_check:
        inmate_name = str(inmate.name).strip().lower()
        inmate_identifier = (inmate_name, inmate.arrest_date)

        # Check if this specific incarceration (name + arrest_date) is still in current inmates list
        if inmate_identifier not in current_inmate_identifiers:
            # This specific incarceration not found in current scrape - likely released
            # Use their last_seen date as the release date
            if inmate.last_seen:
                # Extract just the date part from the datetime object
                release_date_str = inmate.last_seen.date().isoformat()
            else:
                # Fallback to today's date if no last_seen
                release_date_str = today.isoformat()
            
            logger.info(
                f"Setting release date for {inmate.name} (arrested: {inmate.arrest_date}) to {release_date_str} (last seen: {inmate.last_seen})"
            )
            
            inmate.release_date = release_date_str
            updated_count += 1
        else:
            logger.debug(f"Inmate {inmate.name} (arrested: {inmate.arrest_date}) still in current roster, skipping release date update")

    if updated_count > 0:
        logger.info(f"Updated release dates for {updated_count} inmates in {jail.jail_name}")
    else:
        logger.debug(f"No release date updates needed in {jail.jail_name}")


# Backward compatibility
def process_scrape_data(session: Session, inmates: List[Inmate], jail: Jail):
    """
    Backward compatible wrapper that uses the optimized processor.
    """
    return process_scrape_data_optimized(session, inmates, jail)
