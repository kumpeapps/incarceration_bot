"""Web Scraper for Crawford County AR Jail"""

from datetime import datetime
import requests  # type: ignore
import bs4  # type: ignore

from sqlalchemy.orm import Session
from loguru import logger
from models.Jail import Jail
from models.Inmate import Inmate

from scrapes.process import process_scrape_data

URL = "https://inmates.crawfordcountysheriff.org"


def scrape_inmate_data(details_path: str) -> dict:
    """
    Extract detailed inmate information from individual inmate pages.

    This function retrieves and parses the HTML from an inmate's detail page,
    extracting information such as name, ID, race, sex, height, weight,
    residence, booking date, arresting agency, and charges with bond amounts.

    Args:
        details_path (str): The URL path to the inmate's detail page.

    Returns:
        dict: A dictionary containing the parsed inmate information with keys for
        name, inmate_id, race, sex, height, weight, residence, booking_date,
        arresting_agency, and charges.
    """
    details_url = f"{URL}{details_path}"
    req = requests.get(details_url, timeout=30)
    soup = bs4.BeautifulSoup(req.text, "html.parser")
    inmate_table = soup.find_all("table")[0]
    inmate_rows = inmate_table.find_all("tr")
    name = inmate_rows[0].text.strip()
    inmate_id = inmate_rows[1].text.strip()
    race = inmate_rows[2].text.strip()
    sex = inmate_rows[3].text.strip()
    height = inmate_rows[4].text.strip()
    weight = inmate_rows[5].text.strip()
    residence = inmate_rows[6].text.strip()
    booking_date = inmate_rows[8].text.strip()
    arresting_agency = inmate_rows[9].text.strip()
    charges_table = soup.find_all("table")[1]
    charges_rows = charges_table.find_all("tr")
    charges = ""
    for charge_row in charges_rows[1:]:
        charge_cells = charge_row.find_all("td")
        charge = charge_cells[0].text.strip()
        bond = charge_cells[1].text.strip()
        charges += f"{charge} - Bond: {bond}\n"
    details: dict = {
        "name": name,
        "inmate_id": inmate_id,
        "race": race,
        "sex": sex,
        "height": height,
        "weight": weight,
        "residence": residence,
        "booking_date": booking_date,
        "arresting_agency": arresting_agency,
        "charges": charges,
    }
    return details


def scrape_crawford_so_ar(session: Session, jail: Jail, log_level: str = "INFO") -> None:
    """
    Get Crawford County Inmate Data.

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
        details_path = cells[0].find("a")["href"]
        name = name.replace("&nbsp", " ")
        # age = cells[1].text.strip()
        race = cells[1].text.strip()
        sex = cells[2].text.strip()
        sex = "Male" if sex == "M" else "Female" if sex == "F" else sex
        details = scrape_inmate_data(details_path)

        arrest_date = None
        # Clean up the booking date by removing any prefix
        cleaned_booking_date = (
            details["booking_date"].replace("Booking Date:", "").strip()
        )

        # Try different date formats
        date_formats = [
            "%m/%d/%Y %H:%M",  # 05/03/2025 14:26
            "%m/%d/%Y",  # 05/03/2025
            "%Y-%m-%d %H:%M",  # 2025-05-03 14:26
            "%Y-%m-%d",  # 2025-05-03
        ]

        for date_format in date_formats:
            try:
                arrest_date = datetime.strptime(
                    cleaned_booking_date, date_format
                ).date()
                break
            except ValueError as error:
                logger.debug(f"Failed to parse date '{cleaned_booking_date}' with format '{date_format}': {error}")

        if arrest_date is None:
            logger.warning(
                f"Could not parse booking date: '{details['booking_date']}' (cleaned: '{cleaned_booking_date}') - tried formats: {date_formats}"
            )

        inmate = Inmate(  # pylint: disable=unexpected-keyword-arg
            name=name,
            race=race,
            sex=sex,
            arrest_date=arrest_date,
            jail_id="crawford_so_ar",
            is_juvenile=False,
        )
        inmates.append(inmate)
    logger.debug(inmates)
    logger.success(f"Found {len(inmates)} inmates.")
    process_scrape_data(session, inmates, jail)
