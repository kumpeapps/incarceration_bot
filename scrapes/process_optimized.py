"""Optimized process scraped data"""

from datetime import datetime
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
            if monitor.arrest_date != inmate.arrest_date:
                logger.trace(f"New arrest date for {monitor.name}")
                monitor.arrest_date = inmate.arrest_date
                monitor.last_seen_incarcerated = datetime.now()  # type: ignore
                monitor.send_message(inmate)
                monitors_to_update.append(monitor)
                inmate_processed = True
            elif (
                inmate.release_date
                and monitor.release_date != inmate.release_date
                and inmate.release_date != ""
            ):
                logger.info(f"New release date for {monitor.name}")
                monitor.release_date = inmate.release_date
                monitor.send_message(inmate, released=True)
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

    # Update jail's last scrape date
    try:
        jail.update_last_scrape_date()
        session.commit()
        logger.debug("Updated jail last scrape date")
    except Exception as error:
        logger.error(f"Failed to update jail last scrape date: {error}")
        session.rollback()


# Backward compatibility
def process_scrape_data(session: Session, inmates: List[Inmate], jail: Jail):
    """
    Backward compatible wrapper that uses the optimized processor.
    """
    return process_scrape_data_optimized(session, inmates, jail)
