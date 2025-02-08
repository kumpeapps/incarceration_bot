"""Process scraped data"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from loguru import logger
from models.Jail import Jail
from models.Inmate import Inmate
from models.Monitor import Monitor


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
                if monitor.name != inmate.name:
                    logger.info(f"Checking for full name match for {monitor.name}")
                    full_name_monitor = session.query(Monitor).filter(Monitor.name == inmate.name).first()
                    if full_name_monitor:
                        logger.info(f"Found full name match for {inmate.name}, Skipping partial match")
                        skip = True
                    else:
                        logger.info("No full name match found.")
                if monitor.arrest_date != inmate.arrest_date and not skip:
                    logger.trace(f"New arrest date for {monitor.name}")
                    if monitor.name == inmate.name:
                        logger.trace(f"Found exact match for {monitor.name}")
                        monitor.arrest_date = inmate.arrest_date
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
                        )
                        session.add(new_monitor)
                    monitor.send_message(inmate)
                    try:
                        session.commit()
                    except IntegrityError:
                        session.rollback()
                elif (
                    inmate.release_date
                    and monitor.release_date != inmate.release_date
                    and inmate.release_date != ""
                ):
                    logger.info(f"New release date for {monitor.name}")
                    monitor.release_date = inmate.release_date
                    monitor.send_message(inmate, released=True)
        session.add(inmate)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()

    jail.update_last_scrape_date()
    session.commit()
