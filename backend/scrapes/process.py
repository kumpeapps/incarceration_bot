"""Process scraped data"""

from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from loguru import logger
from models.Jail import Jail
from models.Inmate import Inmate
from models.Monitor import Monitor
from helpers.insert_ignore import insert_ignore


def process_scraped_inmates(session: Session, inmates: list[Inmate], jail: Jail):
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
    
    # Track processed inmate-monitor combinations to avoid duplicate notifications
    processed_combinations = set()
    
    for inmate in inmates:
        # First, find all exact matches and notify all users
        exact_matches = [m for m in monitors if m.name == inmate.name]
        
        if exact_matches:
            logger.info(f"Found {len(exact_matches)} exact match(es) for {inmate.name}")
            for monitor in exact_matches:
                combination_key = f"{inmate.name}_{monitor.id}_{inmate.arrest_date}"
                if combination_key in processed_combinations:
                    continue
                processed_combinations.add(combination_key)
                
                logger.info(f"Processing exact match: {monitor.name} (Monitor ID: {monitor.id}, User ID: {monitor.user_id})")
                
                # Always update last_seen_incarcerated for exact matches
                monitor.last_seen_incarcerated = datetime.now()  # type: ignore
                
                # Check for new arrest
                if monitor.arrest_date != inmate.arrest_date:
                    logger.trace(f"New arrest date for {monitor.name} (Monitor ID: {monitor.id})")
                    monitor.arrest_date = inmate.arrest_date
                    monitor.last_seen_incarcerated = datetime.now() # type: ignore
                    monitor.send_message(inmate)
                    try:
                        session.commit()
                    except IntegrityError as error:
                        logger.debug(f"Failed to commit monitor update: {error}")
                        session.rollback()
                
                # Check for release
                elif (
                    inmate.release_date
                    and monitor.release_date != inmate.release_date
                    and inmate.release_date != ""
                ):
                    logger.info(f"New release date for {monitor.name} (Monitor ID: {monitor.id})")
                    monitor.release_date = inmate.release_date
                    monitor.send_message(inmate, released=True)
        
        # Then, handle partial matches only if no exact matches exist
        else:
            for monitor in monitors:
                if monitor.name in inmate.name and monitor.name != inmate.name:
                    combination_key = f"{inmate.name}_{monitor.id}_{inmate.arrest_date}"
                    if combination_key in processed_combinations:
                        continue
                    processed_combinations.add(combination_key)
                    
                    logger.info(f"Processing partial match: {monitor.name} -> {inmate.name} (Monitor ID: {monitor.id})")
                    
                    # Always update last_seen_incarcerated for partial matches
                    monitor.last_seen_incarcerated = datetime.now()  # type: ignore
                    
                    if monitor.arrest_date != inmate.arrest_date:
                        logger.trace(f"New arrest date for partial match {monitor.name}")
                        logger.success(f"Creating new monitor for {inmate.name} based on partial match")
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
                            user_id=monitor.user_id  # Keep same user for the new monitor
                        )
                        session.add(new_monitor)
                        monitor.send_message(inmate)
                        try:
                            session.commit()
                        except IntegrityError as error:
                            logger.debug(f"Failed to commit new monitor: {error}")
                            session.rollback()
        
        # Insert the inmate record
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
            logger.info(f"Monitor {monitor.name} (ID: {monitor.id}, User ID: {monitor.user_id}) appears to have been released from {jail.jail_name}")
            
            # Set release date to today since we don't have the exact date
            release_date_str = datetime.now().strftime("%Y-%m-%d")
            logger.info(f"Setting release date for {monitor.name} (Monitor ID: {monitor.id}) to: '{release_date_str}'")
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
                logger.success(f"Sent release notification for {monitor.name} (Monitor ID: {monitor.id}, User ID: {monitor.user_id})")
            except Exception as error:
                logger.error(f"Failed to send release notification for {monitor.name} (Monitor ID: {monitor.id}): {error}")
            
            released_monitors.append(monitor)
    
    if released_monitors:
        logger.info(f"Marked {len(released_monitors)} monitors as released from {jail.jail_name}")
    else:
        logger.debug(f"No releases detected in {jail.jail_name}")
