"""Web Scraper for Aiken County SC Jail"""

from datetime import datetime
import re
import time
import requests  # type: ignore
import bs4  # type: ignore
from sqlalchemy.orm import Session
from loguru import logger
from models.Jail import Jail
from models.Inmate import Inmate
from scrapes.process_optimized import process_scrape_data
from helpers.image_helper import image_url_to_base64

# Base URLs
SEARCH_URL = "https://www.aikencountysc.gov/DTNSearch/DtnSchInmDspPublic_newFlex.php"
BASE_URL = "https://www.aikencountysc.gov/DTNSearch"
MUGSHOT_BASE_URL = "https://www.aikencountysc.gov"

def parse_date(date_str):
    """Parse date from string format MM-DD-YYYY"""
    if not date_str or date_str.strip() == "":
        return None
    
    try:
        return datetime.strptime(date_str.strip(), "%m-%d-%Y").date()
    except ValueError:
        logger.warning(f"Could not parse date: {date_str}")
        return None

def get_inmate_details(inmate_id):
    """
    Get detailed information for a specific inmate
    
    Args:
        inmate_id: The inmate ID to look up
        
    Returns:
        dict: Inmate details including charges and mugshot
    """
    details_url = f"{BASE_URL}/DtnDspPerDtlPublicFlex.php?qSO_NO={inmate_id}"
    
    try:
        response = requests.get(details_url, timeout=30)
        response.raise_for_status()
        
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        
        # Get mugshot if available
        mugshot = None
        mugshot_tag = soup.select('img[src^="/FlexImages/"]')
        if mugshot_tag and len(mugshot_tag) > 0:
            mugshot_url = mugshot_tag[0]['src']
            full_mugshot_url = f"{MUGSHOT_BASE_URL}{mugshot_url}"
            mugshot = image_url_to_base64(full_mugshot_url)
        
        # Get name and clean it up
        name_tag = soup.find("b", style="color:#dc0023")
        name = name_tag.text.strip() if name_tag else ""
        
        # Get charges
        charges = []
        charge_elements = soup.find_all("td", string=lambda s: s and "Charge:" in s)
        for charge_element in charge_elements:
            charge_text = charge_element.text.strip()
            # Extract the actual charge text
            charge_match = re.search(r'Charge:\s*(.*?)(?:\s*Case #:|$)', charge_text)
            if charge_match:
                charges.append(charge_match.group(1).strip())
        
        hold_reasons = ", ".join(charges)
        
        # Get bio info
        bio_table = soup.find("h3", string="Bio:").find_next("table")
        
        # Parse race and sex
        race = "Unknown"
        sex = "Unknown"
        bio_cells = bio_table.find_all("td")
        if bio_cells:
            bio_text = bio_cells[0].text
            sex_match = re.search(r'Sex:\s*(\w)', bio_text)
            race_match = re.search(r'Race:\s*(\w)', bio_text)
            
            if sex_match:
                sex = sex_match.group(1)
            if race_match:
                race = race_match.group(1)
        
        # Parse arrest date
        arrest_date = None
        arrest_table = soup.find("h3", string="Arrest Details").find_next("table")
        if arrest_table:
            date_cells = arrest_table.find_all("td", align="center")
            if len(date_cells) >= 3:  # Agency, Status, Date
                date_text = date_cells[2].text.strip()
                date_match = re.search(r'(\d{2}-\d{2}-\d{4})', date_text)
                if date_match:
                    arrest_date = parse_date(date_match.group(1))
        
        # Return complete inmate object
        return {
            "name": name,
            "inmate_id": inmate_id,
            "race": race,
            "sex": sex,
            "arrest_date": arrest_date,
            "mugshot": mugshot,
            "hold_reasons": hold_reasons
        }
        
    except Exception as e:
        logger.exception(f"Error getting details for inmate {inmate_id}: {str(e)}")
        return None

def get_all_inmates():
    """
    Get all inmates currently in custody
    
    Returns:
        list: List of inmates with basic info
    """
    inmates = []
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    # Loop through each letter of the alphabet to get all inmates
    for letter in alphabet:
        logger.info(f"Searching inmates with last names starting with '{letter}'")
        
        search_params = {
            "LNAME": letter,
            "FNAME": "",
            "InSex": "All",
            "InRace": "All",
        }
        
        try:
            # Add a small delay to avoid overwhelming the server
            time.sleep(1)
            
            response = requests.post(SEARCH_URL, data=search_params, timeout=30)
            response.raise_for_status()
            
            soup = bs4.BeautifulSoup(response.text, "html.parser")
            
            # Find all inmate rows in the results table
            inmate_links = soup.find_all("a", href=lambda href: href and "qSO_NO=" in href)
            logger.debug(f"Found {len(inmate_links)} inmates with last names starting with '{letter}'")
            
            # Process each inmate
            for link in inmate_links:
                try:
                    # Extract inmate ID from the link
                    inmate_id = re.search(r'qSO_NO=(\d+)', link['href']).group(1)
                    
                    # Get the row that contains this link
                    row = link.find_parent("tr")
                    cells = row.find_all("td")
                    
                    if len(cells) >= 6:  # Make sure we have all the columns
                        last_name = cells[0].text.strip()
                        first_name = cells[1].text.strip()
                        arrest_date = parse_date(cells[2].text.strip())
                        sex = cells[4].text.strip()
                        race = cells[5].text.strip()
                        
                        # Get detailed info
                        # Add a small delay before fetching details
                        time.sleep(0.5)
                        inmate_details = get_inmate_details(inmate_id)
                        
                        if inmate_details:
                            inmates.append(inmate_details)
                        
                except Exception as e:
                    logger.exception(f"Error processing inmate row: {str(e)}")
                    continue
                
        except Exception as e:
            logger.exception(f"Error fetching inmates for letter {letter}: {str(e)}")
    
    logger.info(f"Total inmates found across all letters: {len(inmates)}")
    return inmates

def scrape_aiken_so_sc(session: Session, jail: Jail):
    """
    Get Inmate Records from Aiken County SC Jail.
    
    Args:
        session (Session): SQLAlchemy session for database operations.
        jail (Jail): Jail object containing jail details.
        
    Returns:
        None
    """
    logger.info(f"Scraping {jail.jail_name}")
    
    inmate_list = []
    
    # Get all inmates
    inmates = get_all_inmates()
    
    for inmate_data in inmates:
        try:
            new_inmate = Inmate(
                name=inmate_data["name"],
                arrest_date=inmate_data["arrest_date"],
                release_date=None,  # No release date for current inmates
                hold_reasons=inmate_data["hold_reasons"],
                held_for_agency=None,  # This info isn't clearly available
                jail_id=jail.jail_id,
                race=inmate_data["race"],
                sex=inmate_data["sex"],
                cell_block=None,  # Not available
                mugshot=inmate_data["mugshot"],
                is_juvenile=False,  # Not clear how to determine this
            )
            inmate_list.append(new_inmate)
        except Exception as e:
            logger.exception(f"Error creating inmate object: {str(e)}")
    
    # Process the scraped data
    process_scrape_data(session, inmate_list, jail)
    logger.info(f"Completed scraping {jail.jail_name}")
