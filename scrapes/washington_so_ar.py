"""Web Scraper for Washington County AR Jail"""

from datetime import datetime
import requests  # type: ignore
import bs4  # type: ignore
from sqlalchemy.orm import Session
from loguru import logger
from models.Jail import Jail
from models.Inmate import Inmate
from scrapes.process import process_scrape_data
from helpers.image_helper import image_url_to_base64

URL = "https://www.washcosoar.gov/res/DetaineeAlphaRoster.aspx"


def scrape_inmate_data(details_path: str) -> dict:
    """
    Scrape detailed inmate information from a specific inmate's detail page.

    This function retrieves the mugshot, charges, and responsible department
    for an inmate from their detail page.

    Args:
        details_path (str): URL to the inmate's detail page.

    Returns:
        dict: Dictionary containing the inmate's details with the following keys:
            - mugshot: Base64 encoded string of the inmate's mugshot.
            - charges: String containing all charges and bond amounts.
            - department: String identifying the department responsible for the inmate.
    """
    req = requests.get(details_path, timeout=30)
    soup = bs4.BeautifulSoup(req.text, "html.parser")
    images = soup.find_all("img")
    mugshot_url = images[4]["src"]
    mugshot_url = f"https://www.washcosoar.gov/{mugshot_url}"
    mugshot = image_url_to_base64(mugshot_url)
    inmate_table = soup.find_all("table")[0]
    inmate_rows = inmate_table.find_all("tr")
    charges = ""
    department = ""
    for charge_row in inmate_rows[1:]:
        charge_cells = charge_row.find_all("td")
        charge = charge_cells[0].text.strip()
        bond = charge_cells[1].text.strip()
        charges += f"{charge} - {bond}\n"
        department = charge_cells[3].text.strip()
    details = {
        "mugshot": mugshot,
        "charges": charges,
        "department": department,
    }
    return details


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
    logger.debug(f"Found {len(rows)} rows in the table.")
    for row in rows[2:]:
        cells = row.find_all("td")
        name = cells[0].text.strip()
        logger.debug(f"Scraping inmate: {name}")
        # age = cells[1].text.strip()
        race = cells[2].text.strip()
        sex = cells[3].text.strip()
        sex = "Male" if sex == "M" else "Female" if sex == "F" else sex
        # prior_bookings = cells[4].text.strip()
        intake = cells[5].text.strip()
        # bond = cells[6].text.strip()
        urls = row.find_all("a")
        details_url = urls[0]["href"]
        details_url = f"https://www.washcosoar.gov/res/{details_url}"
        details = scrape_inmate_data(details_url)
        try:
            arrest_date = datetime.strptime(intake, "%m/%d/%Y %H:%M").date()
        except ValueError:
            arrest_date = None
        inmate = Inmate(  # pylint: disable=unexpected-keyword-arg
            name=name,
            race=race,
            sex=sex,
            arrest_date=arrest_date,
            jail_id=jail.jail_id,
            is_juvenile=False,
            mugshot=details["mugshot"],
            held_for_agency=details["department"],
            hold_reasons=details["charges"],
        )
        inmates.append(inmate)
        logger.debug(f"Added inmate: {name} with arrest date: {arrest_date}")
    logger.success(f"Found {len(inmates)} inmates.")
    process_scrape_data(session, inmates, jail)
