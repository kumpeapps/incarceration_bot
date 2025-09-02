"""Scrape Zuercher Portal for Inmate Records"""

import os
from datetime import datetime, date
import zuercherportal_api as zuercherportal  # type: ignore
from sqlalchemy.orm import Session
from loguru import logger
from zuercherportal_api import ZuercherportalResponse
from models.Jail import Jail
from models.Inmate import Inmate
from scrapes.process_optimized import process_scrape_data


def scrape_zuercherportal(session: Session, jail: Jail):
    """
    Get Inmate Records from a Zuercher Portal.

    Args:
        session (Session): SQLAlchemy session for database operations.
        jail (Jail): Jail object containing jail details.

    Returns:
        None
    """
    # Get LOG_LEVEL from environment variable to pass to zuercherportal API
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    logger.info(f"Scraping {jail.jail_name}")
    jail_api = zuercherportal.API(jail.jail_id, log_level=log_level, return_object=True)
    inmate_data: ZuercherportalResponse = jail_api.inmate_search(records_per_page=10000)
    inmate_list: list[Inmate] = []
    for inmate in inmate_data.records:
        try:
            arrest_date = datetime.strptime(inmate.arrest_date, "%Y-%m-%d").date()
        except ValueError:
            arrest_date = None
        try:
            release_date = datetime.strptime(inmate.release_date, "%Y-%m-%d").date().strftime("%Y-%m-%d")
        except ValueError:
            release_date = ""
        new_inmate = Inmate(  # pylint: disable=unexpected-keyword-arg
            name=inmate.name,
            arrest_date=arrest_date,
            release_date=release_date,
            hold_reasons=inmate.hold_reasons,
            held_for_agency=inmate.held_for_agency,
            jail_id=jail.jail_id,
            race=inmate.race,
            sex=inmate.sex,
            cell_block=inmate.cell_block,
            mugshot=inmate.mugshot,
            is_juvenile=inmate.is_juvenile,
            dob="Unknown",
            in_custody_date=date.today(),
            hide_record=False,
        )
        inmate_list.append(new_inmate)
    process_scrape_data(session, inmate_list, jail)
