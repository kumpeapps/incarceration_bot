"""Process scraped data"""


from typing import Optional
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
            if monitor.name in inmate.name:
                logger.info(f"Matched {monitor.name} to {inmate.name}")
                if monitor.arrest_date != inmate.arrest_date:
                    logger.trace(f"New arrest date for {monitor.name}")
                    compare_name: Optional[Monitor] = session.query(Monitor).filter(Monitor.name == inmate.name).first()
                    if compare_name and compare_name.name == inmate.name:
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
