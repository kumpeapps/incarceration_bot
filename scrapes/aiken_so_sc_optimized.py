"""Optimized Web Scraper for Aiken County SC Jail"""

import os
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
MAX_CONCURRENT_REQUESTS = 10  # Increased from 5 to speed up processing
REQUEST_TIMEOUT = 15  # Shorter timeout to avoid hanging
FETCH_MUGSHOTS = os.getenv("FETCH_MUGSHOTS", "False") == "True"

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
        async with session.get(details_url, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as response:
            if response.status != 200:
                logger.warning(f"Failed to fetch inmate details for {inmate_id}: HTTP {response.status}")
                return None
                
            text = await response.text()
            soup = bs4.BeautifulSoup(text, "html.parser")
            
            # Get mugshot if available - but only store the URL for now
            mugshot = None
            mugshot_url = None
            mugshot_tag = soup.select('img[src^="/FlexImages/"]')
            if FETCH_MUGSHOTS and mugshot_tag and len(mugshot_tag) > 0:
                mugshot_url = mugshot_tag[0]['src']
                
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
                    charge = charge_match.group(1).strip()
                    if charge:  # Only add non-empty charges
                        charges.append(charge)
            
            # Fallback: If no charges found using the above method, try to find them in a different way
            if not charges:
                charge_rows = soup.find_all("tr", {"valign": "top"})
                for row in charge_rows:
                    cells = row.find_all("td")
                    if len(cells) >= 2:
                        for cell in cells:
                            if "Charge:" in cell.text:
                                charge_text = cell.text.strip()
                                charge_match = re.search(r'Charge:\s*(.*?)(?:\s*Case #:|$)', charge_text)
                                if charge_match:
                                    charge = charge_match.group(1).strip()
                                    if charge:
                                        charges.append(charge)
            
            # If still no charges found, look for offense information
            if not charges:
                offense_elements = soup.find_all("td", string=lambda s: s and "Offense:" in s)
                for offense_element in offense_elements:
                    offense_text = offense_element.text.strip()
                    offense_match = re.search(r'Offense:\s*(.*?)(?:\s*\||$)', offense_text)
                    if offense_match:
                        offense = offense_match.group(1).strip()
                        if offense:
                            charges.append(offense)
            
            hold_reasons = ", ".join(charges) if charges else "Unknown"
            
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
            arrest_table = soup.find("h3", string="Arrest Details")
            if arrest_table:
                arrest_table = arrest_table.find_next("table")
                if arrest_table:
                    # Process date
                    date_cells = arrest_table.find_all("td", align="center")
                    if len(date_cells) >= 3:  # Agency, Status, Date
                        date_text = date_cells[2].text.strip()
                        date_match = re.search(r'(\d{2}-\d{2}-\d{4})', date_text)
                        if date_match:
                            arrest_date = parse_date(date_match.group(1))
                    
                    # Get the agency information - first try the center-aligned cells
                    if len(date_cells) >= 1:  # First cell should be Agency
                        agency_text = date_cells[0].text.strip()
                        # Clean up and extract just the agency name
                        agency_match = re.search(r'Agency:\s*(.*?)(?:\s*$)', agency_text)
                        if agency_match:
                            held_for_agency = agency_match.group(1).strip()
            
            # If we couldn't find the agency in the expected place, try alternative approaches
            if not held_for_agency or held_for_agency == "":
                # Method 2: Look for agency label directly
                agency_elements = soup.find_all("td", string=lambda s: s and "Agency:" in s)
                for agency_element in agency_elements:
                    agency_text = agency_element.text.strip()
                    agency_match = re.search(r'Agency:\s*(.*?)(?:\s*$)', agency_text)
                    if agency_match:
                        agency = agency_match.group(1).strip()
                        if agency:
                            held_for_agency = agency
                            break
                
                # Method 3: Look in all table cells for Agency: pattern
                if not held_for_agency or held_for_agency == "":
                    all_cells = soup.find_all("td")
                    for cell in all_cells:
                        cell_text = cell.text.strip()
                        if "Agency:" in cell_text:
                            agency_match = re.search(r'Agency:\s*(.*?)(?:\s*$|[\r\n])', cell_text)
                            if agency_match:
                                agency = agency_match.group(1).strip()
                                if agency:
                                    held_for_agency = agency
                                    break
            
            # Set default if still not found
            if not held_for_agency or held_for_agency == "":
                held_for_agency = "Aiken County Sheriff's Office"  # Default agency
            
            # Only fetch the mugshot if enabled and we have a valid inmate record
            if FETCH_MUGSHOTS and name and mugshot_url:
                full_mugshot_url = f"{MUGSHOT_BASE_URL}{mugshot_url}"
                try:
                    # Use a thread to fetch the image to avoid blocking
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(image_url_to_base64, full_mugshot_url)
                        mugshot = future.result(timeout=5)  # Reduced timeout from 10 to 5 seconds
                except Exception as e:
                    logger.warning(f"Failed to fetch mugshot for inmate {inmate_id}: {str(e)}")
                    mugshot = None
            
            # Return complete inmate object
            inmate_data = {
                "name": name,
                "inmate_id": inmate_id,
                "race": race,
                "sex": sex,
                "arrest_date": arrest_date,
                "mugshot": mugshot,
                "hold_reasons": hold_reasons,
                "held_for_agency": held_for_agency
            }
            
            # Log the values we're especially concerned about
            logger.debug(f"Inmate {inmate_id} - hold_reasons: '{hold_reasons}'")
            logger.debug(f"Inmate {inmate_id} - held_for_agency: '{held_for_agency}'")
            
            return inmate_data
            
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
    logger.info("Starting inmate data collection process")
    start_time = time.time()
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    all_inmates: List[Dict[str, Any]] = []
    
    # Step 1: Get all inmate IDs for each letter in parallel
    logger.info("Collecting inmate IDs for each letter of the alphabet")
    letter_start_time = time.time()
    tasks = []
    for letter in alphabet:
        # Add a small delay to avoid hitting the server too hard
        await asyncio.sleep(0.1)  # Reduced from 0.2 to speed up
        tasks.append(get_inmate_ids_for_letter(letter))
    
    letter_results = await asyncio.gather(*tasks)
    letter_elapsed = time.time() - letter_start_time
    logger.info(f"Completed collecting inmate IDs in {letter_elapsed:.2f} seconds")
    
    # Flatten the list of lists
    basic_inmates = []
    for letter_inmates in letter_results:
        basic_inmates.extend(letter_inmates)
    
    logger.info(f"Found {len(basic_inmates)} inmates in initial search")
    
    # Step 2: Get detailed information for each inmate in parallel with rate limiting
    logger.info("Starting to fetch detailed inmate information")
    details_start_time = time.time()
    
    # Create batches to process inmates in smaller groups
    batch_size = 50
    batches = [basic_inmates[i:i + batch_size] for i in range(0, len(basic_inmates), batch_size)]
    logger.info(f"Processing inmates in {len(batches)} batches of {batch_size}")
    
    all_inmate_details = []
    
    for batch_num, batch in enumerate(batches):
        batch_start_time = time.time()
        logger.info(f"Processing batch {batch_num+1}/{len(batches)} with {len(batch)} inmates")
        
        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
            
            async def get_details_with_semaphore(inmate, index):
                async with semaphore:
                    # Add a small delay between requests
                    await asyncio.sleep(0.05)  # Reduced from 0.1
                    try:
                        return await async_get_inmate_details(session, inmate["inmate_id"])
                    except Exception as e:
                        logger.error(f"Error in batch {batch_num+1}, inmate {index}: {str(e)}")
                        return None
            
            detail_tasks = [get_details_with_semaphore(inmate, i) for i, inmate in enumerate(batch)]
            batch_details = await asyncio.gather(*detail_tasks, return_exceptions=False)
            
            # Filter out None values (failed requests)
            valid_details = [inmate for inmate in batch_details if inmate is not None]
            all_inmate_details.extend(valid_details)
            
            batch_elapsed = time.time() - batch_start_time
            logger.info(f"Completed batch {batch_num+1}/{len(batches)} in {batch_elapsed:.2f} seconds. Got {len(valid_details)}/{len(batch)} inmates.")
    
    details_elapsed = time.time() - details_start_time
    logger.info(f"Completed fetching all inmate details in {details_elapsed:.2f} seconds")
    
    # Filter out None values (failed requests)
    inmates = all_inmate_details
    
    total_elapsed = time.time() - start_time
    logger.info(f"Successfully fetched details for {len(inmates)} inmates in total {total_elapsed:.2f} seconds")
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
    
    try:
        # Get all inmates with optimized async fetching
        logger.info("Starting inmate data collection")
        fetch_start = time.time()
        inmates = get_all_inmates()
        fetch_elapsed = time.time() - fetch_start
        logger.info(f"Found {len(inmates)} inmates to process in {fetch_elapsed:.2f} seconds")
        
        if not inmates:
            logger.warning("No inmates found - check if the website structure has changed")
            # Update the jail record to mark as scraped even if no inmates found
            # These should be objects not Columns, so this is just a linting error in your IDE
            jail.last_scrape_date = datetime.now().date()  # type: ignore
            jail.last_successful_scrape = datetime.now()  # type: ignore
            session.commit()
            logger.info(f"No inmates found for {jail.jail_name}, but marked as scraped")
            return
        
        # Process inmate data into Inmate objects
        logger.info("Creating inmate objects")
        process_start = time.time()
        for inmate_data in inmates:
            try:
                # Add extra logging to verify data
                logger.info(f"Processing inmate: {inmate_data['name']} ({inmate_data['inmate_id']})")
                logger.info(f"  - held_for_agency: '{inmate_data['held_for_agency']}'")
                logger.info(f"  - hold_reasons: '{inmate_data['hold_reasons']}'")
                
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
        
        process_elapsed = time.time() - process_start
        logger.info(f"Created {len(inmate_list)} inmate objects in {process_elapsed:.2f} seconds")
        
        # Process the scraped data with optimized method
        logger.info("Saving inmates to database")
        db_start = time.time()
        process_scrape_data_optimized(session, inmate_list, jail)
        db_elapsed = time.time() - db_start
        logger.info(f"Saved inmates to database in {db_elapsed:.2f} seconds")
        
    except Exception as e:
        logger.exception(f"Error in scraping process: {str(e)}")
    finally:
        elapsed_time = time.time() - start_time
        logger.info(f"Completed optimized scraping of {jail.jail_name} in {elapsed_time:.2f} seconds")
