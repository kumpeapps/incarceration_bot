"""Optimized process scraped data"""

from datetime import datetime, date
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from loguru import logger
from models.Jail import Jail
from models.Inmate import Inmate
from models.Monitor import Monitor
from helpers.insert_ignore import insert_ignore


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
                            release_date=inmate.release_date,
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

        # Always try to insert the inmate record
        inmates_to_insert.append(inmate)

    # Batch database operations
    try:
        # Add new monitors
        if new_monitors:
            logger.info(f"Adding {len(new_monitors)} new monitors")
            for monitor in new_monitors:
                session.add(monitor)

        # Insert inmates in batch
        if inmates_to_insert:
            logger.info(f"Inserting {len(inmates_to_insert)} inmates")
            try:
                for inmate in inmates_to_insert:
                    insert_ignore(session, Inmate, inmate.to_dict())
                    logger.debug(f"Inserted inmate: {inmate.name}")
            except NotImplementedError:
                logger.warning(
                    "insert_ignore not implemented, falling back to bulk_save_objects for inmates batch insert"
                )
                try:
                    session.bulk_save_objects(inmates_to_insert)
                    logger.debug(
                        f"Bulk inserted {len(inmates_to_insert)} inmates with bulk_save_objects"
                    )
                except IntegrityError as error:
                    logger.error(f"Bulk insert failed: {error}")
                    session.rollback()

        # Commit all changes at once
        session.commit()
        logger.info("Successfully committed all changes")

    except Exception as error:
        logger.error(f"Failed to commit changes: {error}")
        session.rollback()
        raise

    # Check for released inmates (those no longer in jail)
    try:
        check_for_released_inmates(session, inmates, jail)
        session.commit()
        logger.debug("Checked for released inmates")
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

            # Set release date to today since we don't have the exact date
            release_date_str = datetime.now().strftime("%Y-%m-%d")
            logger.info(f"Setting release date for {monitor.name} to: '{release_date_str}'")
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


# Backward compatibility
def process_scrape_data(session: Session, inmates: List[Inmate], jail: Jail):
    """
    Backward compatible wrapper that uses the optimized processor.
    """
    return process_scrape_data_optimized(session, inmates, jail)
