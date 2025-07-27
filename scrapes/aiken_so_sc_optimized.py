"""Optimized Web Scraper for Aiken County SC Jail"""

from datetime import datetime
import re
import time
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Any
import requests  # type: ignore
import bs4  # type: ignore
from sqlalchemy.orm import Session
from loguru import logger
from models.Jail import Jail
from models.Inmate import Inmate
from scrapes.process_optimized import process_scrape_data_optimized
from helpers.image_helper import image_url_to_base64

# Base URLs
SEARCH_URL = "https://www.aikencountysc.gov/DTNSearch/DtnSchInmDspPublic_newFlex.php"
BASE_URL = "https://www.aikencountysc.gov/DTNSearch"
MUGSHOT_BASE_URL = "https://www.aikencountysc.gov"
MAX_CONCURRENT_REQUESTS = 5  # Limit concurrent requests to avoid overwhelming server

def parse_date(date_str):
    """Parse date from string format MM-DD-YYYY"""
    if not date_str or date_str.strip() == "":
        return None
    
    try:
        return datetime.strptime(date_str.strip(), "%m-%d-%Y").date()
    except ValueError:
        logger.warning(f"Could not parse date: {date_str}")
        return None

async def async_get_inmate_details(session: aiohttp.ClientSession, inmate_id: str) -> Optional[Dict[str, Any]]:
    """
    Asynchronously get detailed information for a specific inmate
    
    Args:
        session: Async HTTP client session
        inmate_id: The inmate ID to look up
        
    Returns:
        dict: Inmate details including charges, mugshot, and held_for_agency
    """
    details_url = f"{BASE_URL}/DtnDspPerDtlPublicFlex.php?qSO_NO={inmate_id}"
    
    try:
        async with session.get(details_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status != 200:
                logger.warning(f"Failed to fetch inmate details for {inmate_id}: HTTP {response.status}")
                return None
                
            text = await response.text()
            soup = bs4.BeautifulSoup(text, "html.parser")
            
            # Get mugshot if available
            mugshot = None
            mugshot_tag = soup.select('img[src^="/FlexImages/"]')
            if mugshot_tag and len(mugshot_tag) > 0:
                mugshot_url = mugshot_tag[0]['src']
                full_mugshot_url = f"{MUGSHOT_BASE_URL}{mugshot_url}"
                # We'll fetch the image in a separate thread to avoid blocking
                mugshot = None  # We'll fetch it later if needed
                
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
            
            # Parse arrest date and held_for_agency
            arrest_date = None
            held_for_agency = None
            arrest_table = soup.find("h3", string="Arrest Details").find_next("table")
            if arrest_table:
                # Process date
                date_cells = arrest_table.find_all("td", align="center")
                if len(date_cells) >= 3:  # Agency, Status, Date
                    date_text = date_cells[2].text.strip()
                    date_match = re.search(r'(\d{2}-\d{2}-\d{4})', date_text)
                    if date_match:
                        arrest_date = parse_date(date_match.group(1))
                
                # Get the agency information
                if len(date_cells) >= 1:  # First cell should be Agency
                    agency_text = date_cells[0].text.strip()
                    # Clean up and extract just the agency name
                    agency_match = re.search(r'Agency:\s*(.*?)(?:\s*$)', agency_text)
                    if agency_match:
                        held_for_agency = agency_match.group(1).strip()
            
            # Only fetch the mugshot if we have a valid inmate record
            if name and mugshot_tag and len(mugshot_tag) > 0:
                mugshot_url = mugshot_tag[0]['src']
                full_mugshot_url = f"{MUGSHOT_BASE_URL}{mugshot_url}"
                try:
                    # Use a thread to fetch the image to avoid blocking
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(image_url_to_base64, full_mugshot_url)
                        mugshot = future.result(timeout=10)
                except Exception as e:
                    logger.warning(f"Failed to fetch mugshot for inmate {inmate_id}: {str(e)}")
                    mugshot = None
            
            # Return complete inmate object
            return {
                "name": name,
                "inmate_id": inmate_id,
                "race": race,
                "sex": sex,
                "arrest_date": arrest_date,
                "mugshot": mugshot,
                "hold_reasons": hold_reasons,
                "held_for_agency": held_for_agency
            }
            
    except Exception as e:
        logger.exception(f"Error getting details for inmate {inmate_id}: {str(e)}")
        return None

async def get_inmate_ids_for_letter(letter: str) -> List[Dict[str, Any]]:
    """
    Get basic inmate information for a specific letter
    
    Args:
        letter: The starting letter of last names to search
        
    Returns:
        list: List of inmate IDs with basic info
    """
    basic_inmates = []
    
    search_params = {
        "LNAME": letter,
        "FNAME": "",
        "InSex": "All",
        "InRace": "All",
    }
    
    try:
        # Use requests for the initial search since it's a POST request
        # (easier than setting up aiohttp for this one case)
        response = requests.post(SEARCH_URL, data=search_params, timeout=30)
        response.raise_for_status()
        
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        
        # Find all inmate rows in the results table
        inmate_links = soup.find_all("a", href=lambda href: href and "qSO_NO=" in href)
        logger.debug(f"Found {len(inmate_links)} inmates with last names starting with '{letter}'")
        
        # Process each inmate link to extract basic info and IDs
        for link in inmate_links:
            try:
                # Extract inmate ID from the link
                inmate_id_match = re.search(r'qSO_NO=(\d+)', link['href'])
                if inmate_id_match:
                    inmate_id = inmate_id_match.group(1)
                    
                    # Get the row that contains this link
                    row = link.find_parent("tr")
                    cells = row.find_all("td")
                    
                    if len(cells) >= 6:  # Make sure we have all the columns
                        basic_inmates.append({
                            "inmate_id": inmate_id
                        })
                        
            except Exception as e:
                logger.warning(f"Error extracting inmate ID: {str(e)}")
                continue
                
    except Exception as e:
        logger.exception(f"Error fetching inmates for letter {letter}: {str(e)}")
    
    return basic_inmates

async def get_all_inmates_async() -> List[Dict[str, Any]]:
    """
    Asynchronously get all inmates currently in custody
    
    Returns:
        list: List of inmates with detailed info
    """
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    all_inmates: List[Dict[str, Any]] = []
    
    # Step 1: Get all inmate IDs for each letter in parallel
    tasks = []
    for letter in alphabet:
        # Add a small delay to avoid hitting the server too hard
        await asyncio.sleep(0.2)
        tasks.append(get_inmate_ids_for_letter(letter))
    
    letter_results = await asyncio.gather(*tasks)
    
    # Flatten the list of lists
    basic_inmates = []
    for letter_inmates in letter_results:
        basic_inmates.extend(letter_inmates)
    
    logger.info(f"Found {len(basic_inmates)} inmates in initial search")
    
    # Step 2: Get detailed information for each inmate in parallel with rate limiting
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
        async def get_details_with_semaphore(inmate):
            async with semaphore:
                # Add a small delay between requests
                await asyncio.sleep(0.1)
                return await async_get_inmate_details(session, inmate["inmate_id"])
        
        detail_tasks = [get_details_with_semaphore(inmate) for inmate in basic_inmates]
        inmate_details = await asyncio.gather(*detail_tasks)
        
    # Filter out None values (failed requests)
    inmates = [inmate for inmate in inmate_details if inmate is not None]
    
    logger.info(f"Successfully fetched details for {len(inmates)} inmates")
    return inmates

def get_all_inmates() -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for the async get_all_inmates_async function
    
    Returns:
        list: List of inmates with detailed info
    """
    return asyncio.run(get_all_inmates_async())

def scrape_aiken_so_sc_optimized(session: Session, jail: Jail):
    """
    Get Inmate Records from Aiken County SC Jail using optimized approach.
    
    Args:
        session (Session): SQLAlchemy session for database operations.
        jail (Jail): Jail object containing jail details.
        
    Returns:
        None
    """
    logger.info(f"Optimized scraping of {jail.jail_name}")
    
    start_time = time.time()
    inmate_list = []
    
    # Get all inmates with optimized async fetching
    inmates = get_all_inmates()
    
    logger.info(f"Found {len(inmates)} inmates to process")
    
    # Process inmate data into Inmate objects
    for inmate_data in inmates:
        try:
            new_inmate = Inmate(
                name=inmate_data["name"],
                arrest_date=inmate_data["arrest_date"],
                release_date=None,  # No release date for current inmates
                hold_reasons=inmate_data["hold_reasons"],
                held_for_agency=inmate_data["held_for_agency"],
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
    
    # Process the scraped data with optimized method
    process_scrape_data_optimized(session, inmate_list, jail)
    
    elapsed_time = time.time() - start_time
    logger.info(f"Completed optimized scraping of {jail.jail_name} in {elapsed_time:.2f} seconds")
