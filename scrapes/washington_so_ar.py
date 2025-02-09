"""Web Scraper for Washington County AR Jail"""

from datetime import datetime
import requests # type: ignore
import bs4 # type: ignore
from sqlalchemy.orm import Session
from loguru import logger
from models.Jail import Jail
from models.Inmate import Inmate
from scrapes.process import process_scrape_data

URL = "https://www.washcosoar.gov/res/DetaineeAlphaRoster.aspx"


def scrape_washington_so_ar(session: Session, jail: Jail, log_level: str = "INFO"):
    """
    Get Washington County Inmate Data.

    Args:
        session (Session): SQLAlchemy session for database operations.
        jail (Jail): Jail object containing jail details.
        log_level (str): Logging level for the scraping process. Default is "INFO".

    Returns:
        None
    """
    logger.info(f"Scraping {jail.jail_name}")
    req = requests.get(URL, timeout=30)
    soup = bs4.BeautifulSoup(req.text, "html.parser")
    table = soup.find_all("table")[0]
    rows = table.find_all("tr")
    inmates: list[Inmate] = []
    for row in rows[2:]:
        cells = row.find_all("td")
        name = cells[0].text.strip()
        # age = cells[1].text.strip()
        race = cells[2].text.strip()
        sex = cells[3].text.strip()
        sex = "Male" if sex == "M" else "Female" if sex == "F" else sex
        # prior_bookings = cells[4].text.strip()
        intake = cells[5].text.strip()
        # bond = cells[6].text.strip()
        inmate = Inmate( # pylint: disable=unexpected-keyword-arg
            name=name,
            race=race,
            sex=sex,
            arrest_date=datetime.strptime(intake, "%m/%d/%Y").date() if intake else None,
            jail_id=jail.jail_id,
            is_juvenile=False,
        )
        inmates.append(inmate)
    logger.success(f"Found {len(inmates)} inmates.")
    process_scrape_data(session, inmates, jail)
