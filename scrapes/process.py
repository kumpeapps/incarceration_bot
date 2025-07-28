"""Process scraped data"""

from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from loguru import logger
from models.Jail import Jail
from models.Inmate import Inmate
from models.Monitor import Monitor
from helpers.insert_ignore import insert_ignore


def process_scrape_data(session: Session, inmates: list[Inmate], jail: Jail):
    """
    Process scraped inmate data and update the database.

    Args:
        session (Session): SQLAlchemy session for database operations.
        inmates (list[Inmate]): List of Inmate objects containing scraped data.
        jail (Jail): Jail object containing jail details.

    Returns:
        None
    """
    logger.info(f"Processing {jail.jail_name}")
    monitors = session.query(Monitor).all()
    for inmate in inmates:
        for monitor in monitors:
            skip = False
            if monitor.name in inmate.name:
                logger.info(f"Matched {monitor.name} to {inmate.name}")
                
                # Always update last_seen_incarcerated for exact matches
                if monitor.name == inmate.name:
                    monitor.last_seen_incarcerated = datetime.now()  # type: ignore
                
                if monitor.name != inmate.name:
                    logger.info(f"Checking for full name match for {monitor.name}")
                    full_name_monitor = (
                        session.query(Monitor)
                        .filter(Monitor.name == inmate.name)
                        .first()
                    )
                    if full_name_monitor:
                        logger.info(
                            f"Found full name match for {inmate.name}, Skipping partial match"
                        )
                        skip = True
                    else:
                        logger.info("No full name match found.")
                if monitor.arrest_date != inmate.arrest_date and not skip:
                    logger.trace(f"New arrest date for {monitor.name}")
                    if monitor.name == inmate.name:
                        logger.trace(f"Found exact match for {monitor.name}")
                        monitor.arrest_date = inmate.arrest_date
                        monitor.last_seen_incarcerated = datetime.now() # type: ignore
                    else:
                        logger.trace(f"Found partial match for {monitor.name}.")
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
                        session.add(new_monitor)
                    monitor.send_message(inmate)
                    try:
                        session.commit()
                    except IntegrityError as error:
                        logger.debug(f"Failed to commit new monitor: {error}")
                        session.rollback()
                elif (
                    inmate.release_date
                    and monitor.release_date != inmate.release_date
                    and inmate.release_date != ""
                ):
                    logger.info(f"New release date for {monitor.name}")
                    monitor.release_date = inmate.release_date
                    monitor.send_message(inmate, released=True)
        try:
            insert_ignore(session, Inmate, inmate.to_dict())
            logger.debug(f"Inserted inmate: {inmate.name}")
        except NotImplementedError as error:
            logger.debug(f"Insert ignore not implemented: {error}")
            try:
                session.add(inmate)
            except IntegrityError:
                logger.debug(f"Failed to add inmate: {error}")
                session.rollback()
    session.commit()

    # Check for released inmates (those no longer in jail)
    try:
        check_for_released_inmates(session, inmates, jail)
        session.commit()
        logger.debug("Checked for released inmates")
    except Exception as error:
        logger.error(f"Failed to check for released inmates: {error}")
        session.rollback()

    jail.update_last_scrape_date()
    session.commit()


def check_for_released_inmates(session: Session, current_inmates: list[Inmate], jail: Jail):
    """
    Check for monitors that were previously incarcerated but are no longer
    in the current batch of scraped inmates, indicating they may have been released.
    
    Args:
        session (Session): SQLAlchemy session for database operations.
        current_inmates (list[Inmate]): List of currently scraped inmates.
        jail (Jail): Jail object containing jail details.
    """
    logger.debug(f"Checking for released inmates in {jail.jail_name}")
    
    # Get all monitors for this jail that have been seen incarcerated
    # and don't already have a release date
    monitors_to_check = session.query(Monitor).filter(
        Monitor.jail == jail.jail_name,
        Monitor.last_seen_incarcerated.isnot(None),
        Monitor.release_date.is_(None)
    ).all()
    
    if not monitors_to_check:
        logger.debug(f"No monitors to check for releases in {jail.jail_name}")
        return
    
    logger.debug(f"Found {len(monitors_to_check)} monitors to check for releases")
    
    # Create a set of current inmate names for fast lookup
    current_inmate_names = {str(inmate.name).strip().lower() for inmate in current_inmates}
    
    released_monitors = []
    
    for monitor in monitors_to_check:
        monitor_name = str(monitor.name).strip().lower()
        
        # Check if monitor is still in current inmates list
        if monitor_name not in current_inmate_names:
            # Monitor not found in current inmates - likely released
            logger.info(f"Monitor {monitor.name} appears to have been released from {jail.jail_name}")
            
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
                logger.error(f"Failed to send release notification for {monitor.name}: {error}")
            
            released_monitors.append(monitor)
    
    if released_monitors:
        logger.info(f"Marked {len(released_monitors)} monitors as released from {jail.jail_name}")
    else:
        logger.debug(f"No releases detected in {jail.jail_name}")
