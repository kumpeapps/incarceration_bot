"""Scrape Zuercher Portal for Inmate Records"""

import zuercherportal_api as zuercherportal  # type: ignore
from sqlalchemy.orm import Session
from loguru import logger
from zuercherportal_api import ZuercherportalResponse
from models.Jail import Jail
from models.Inmate import Inmate
from scrapes.process import process_scrape_data


def scrape_zuercherportal(session: Session, jail: Jail, log_level: str = "INFO"):
    """
    Get Inmate Records from a Zuercher Portal.

    Args:
        session (Session): SQLAlchemy session for database operations.
        jail (Jail): Jail object containing jail details.
        log_level (str): Logging level for the scraping process. Default is "INFO".

    Returns:
        None
    """
    logger.info(f"Scraping {jail.jail_name}")
    jail_api = zuercherportal.API(jail.jail_id, log_level=log_level, return_object=True)
    inmate_data: ZuercherportalResponse = jail_api.inmate_search(records_per_page=10000)
    inmate_list: list[Inmate] = []
    for inmate in inmate_data.records:
        new_inmate = Inmate(  # pylint: disable=unexpected-keyword-arg
            name=inmate.name,
            arrest_date=inmate.arrest_date,
            release_date=inmate.release_date,
            hold_reasons=inmate.hold_reasons,
            held_for_agency=inmate.held_for_agency,
            jail_id=jail.jail_id,
            race=inmate.race,
            sex=inmate.sex,
            cell_block=inmate.cell_block,
            mugshot=inmate.mugshot,
            is_juvenile=inmate.is_juvenile,
        )
        inmate_list.append(new_inmate)
    process_scrape_data(session, inmate_list, jail)
