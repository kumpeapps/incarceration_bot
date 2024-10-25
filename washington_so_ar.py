"""Web Scraper for Washington County AR Jail"""

import requests
import bs4
from zuercherportal_api import Inmate

url = "https://www.washcosoar.gov/res/DetaineeAlphaRoster.aspx"


def get_data() -> list:
    """Get Washington County Inmate Data"""
    req = requests.get(url, timeout=30)
    soup = bs4.BeautifulSoup(req.text, "html.parser")
    table = soup.find_all("table")[0]
    rows = table.find_all("tr")
    inmates: [Inmate] = []
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
        inmate: Inmate = Inmate(name, race, sex, "", intake, "", "", "", "", False, "")
        inmates.append(inmate)
    return inmates
