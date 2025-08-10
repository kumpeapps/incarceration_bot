"""Optimized Web Scraper for Washington County AR Jail"""

from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
import time
import asyncio
import aiohttp
import requests  # type: ignore
import bs4  # type: ignore
from sqlalchemy.orm import Session
from loguru import logger
from models.Jail import Jail
from models.Inmate import Inmate
from scrapes.process_optimized import process_scrape_data
from helpers.image_helper import image_url_to_base64


URL = "https://www.washcosoar.gov/res/DetaineeAlphaRoster.aspx"


async def async_scrape_inmate_data(
    session: aiohttp.ClientSession, details_path: str
) -> Optional[Dict]:
    """
    Asynchronously scrape detailed inmate information from a specific inmate's detail page.

    Args:
        session (aiohttp.ClientSession): Async HTTP session.
        details_path (str): URL to the inmate's detail page.

    Returns:
        Dict: Dictionary containing the inmate's details or None if error.
    """
    try:
        async with session.get(
            details_path, timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status != 200:
                logger.warning(
                    f"Failed to fetch {details_path}: HTTP {response.status}"
                )
                return None

            text = await response.text()
            soup = bs4.BeautifulSoup(text, "html.parser")

            images = soup.find_all("img")
            if len(images) < 5:
                logger.warning(f"Not enough images found in {details_path}")
                return None

            mugshot_url = f"https://www.washcosoar.gov/{images[4]['src']}"

            # Get mugshot asynchronously
            mugshot = await async_image_url_to_base64(session, mugshot_url)

            inmate_table = soup.find_all("table")[0]
            inmate_rows = inmate_table.find_all("tr")
            charge_list = []
            department = ""

            for charge_row in inmate_rows[1:]:
                charge_cells = charge_row.find_all("td")
                if len(charge_cells) >= 4:
                    charge = charge_cells[0].text.strip()
                    bond = charge_cells[1].text.strip()
                    charge_list.append(f"{charge} - {bond}")
                    department = charge_cells[3].text.strip()

            charges = "\n".join(charge_list)

            return {
                "mugshot": mugshot,
                "charges": charges,
                "department": department,
            }
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, IndexError) as e:
        logger.error(f"Error scraping inmate data from {details_path}: {e}")
        return None


async def async_image_url_to_base64(
    session: aiohttp.ClientSession, image_url: str
) -> Optional[str]:
    """
    Asynchronously fetch an image and convert to base64.

    Args:
        session (aiohttp.ClientSession): Async HTTP session.
        image_url (str): URL of the image.

    Returns:
        str: Base64 encoded image data or None if error.
    """
    try:
        async with session.get(
            image_url, timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status == 200:
                image_data = await response.read()
                import base64

                return base64.b64encode(image_data).decode("utf-8")
            else:
                logger.warning(
                    f"Failed to fetch image {image_url}: HTTP {response.status}"
                )
                return None
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.error(f"Error fetching image from {image_url}: {e}")
        return None


def scrape_inmate_data_sync(details_path: str) -> Optional[Dict]:
    """
    Synchronous version of inmate data scraping for fallback.
    """
    try:
        req = requests.get(details_path, timeout=30)
        soup = bs4.BeautifulSoup(req.text, "html.parser")
        images = soup.find_all("img")

        if len(images) < 5:
            logger.warning(f"Not enough images found in {details_path}")
            return None

        mugshot_url = f"https://www.washcosoar.gov/{images[4]['src']}"
        mugshot = image_url_to_base64(mugshot_url)

        inmate_table = soup.find_all("table")[0]
        inmate_rows = inmate_table.find_all("tr")
        charge_list = []
        department = ""

        for charge_row in inmate_rows[1:]:
            charge_cells = charge_row.find_all("td")
            if len(charge_cells) >= 4:
                charge = charge_cells[0].text.strip()
                bond = charge_cells[1].text.strip()
                charge_list.append(f"{charge} - {bond}")
                department = charge_cells[3].text.strip()

        charges = "\n".join(charge_list)

        return {
            "mugshot": mugshot,
            "charges": charges,
            "department": department,
        }
    except (requests.RequestException, ValueError, IndexError) as e:
        logger.error(f"Error scraping inmate data from {details_path}: {e}")
        return None


async def async_scrape_all_inmate_details(
    detail_urls: List[str], max_concurrent: int = 10
) -> List[Optional[Dict]]:
    """
    Asynchronously scrape all inmate details with concurrency control.

    Args:
        detail_urls (List[str]): List of detail page URLs.
        max_concurrent (int): Maximum concurrent requests.

    Returns:
        List[Optional[Dict]]: List of inmate details (None for failures).
    """
    connector = aiohttp.TCPConnector(
        limit=max_concurrent, limit_per_host=max_concurrent
    )
    timeout = aiohttp.ClientTimeout(total=60)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_scrape(url):
            async with semaphore:
                return await async_scrape_inmate_data(session, url)

        tasks = [bounded_scrape(url) for url in detail_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to None and log them
        processed_results: List[Optional[Dict]] = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Async scraping failed: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)  # type: ignore

        return processed_results


def scrape_with_threading(
    detail_urls: List[str], max_workers: int = 5
) -> List[Optional[Dict]]:
    """
    Scrape inmate details using ThreadPoolExecutor for I/O bound operations.

    Args:
        detail_urls (List[str]): List of detail page URLs.
        max_workers (int): Maximum number of worker threads.

    Returns:
        List[Optional[Dict]]: List of inmate details.
    """
    results: List[Optional[Dict]] = [None] * len(detail_urls)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_index = {
            executor.submit(scrape_inmate_data_sync, url): i
            for i, url in enumerate(detail_urls)
        }

        # Collect results
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result()
                results[index] = result
            except (requests.RequestException, ValueError, IndexError) as e:
                logger.error(
                    f"Threading scrape failed for URL {detail_urls[index]}: {e}"
                )
                results[index] = None

    return results


def scrape_washington_so_ar_optimized(
    session: Session,
    jail: Jail,
    use_async: bool = True,
    max_concurrent: int = 10,
):
    """
    Optimized version of Washington County Inmate Data scraper.

    Args:
        session (Session): SQLAlchemy session for database operations.
        jail (Jail): Jail object containing jail details.
        use_async (bool): Whether to use async scraping (faster but requires aiohttp).
        max_concurrent (int): Maximum concurrent requests when using async.

    Returns:
        None
    """
    start_time = time.time()
    logger.info(f"Scraping {jail.jail_name} (optimized)")

    # Get main roster page
    req = requests.get(URL, timeout=30)
    soup = bs4.BeautifulSoup(req.text, "html.parser")
    table = soup.find_all("table")[0]
    rows = table.find_all("tr")

    logger.debug(f"Found {len(rows)} rows in the table.")

    # Extract basic inmate info and detail URLs
    basic_inmate_data = []
    detail_urls = []

    for row in rows[2:]:
        cells = row.find_all("td")
        if len(cells) < 6:
            continue

        name = cells[0].text.strip()
        race = cells[2].text.strip()
        sex = cells[3].text.strip()
        sex = {"M": "Male", "F": "Female"}.get(sex, sex)
        intake = cells[5].text.strip()

        urls = row.find_all("a")
        if urls:
            details_url = f"https://www.washcosoar.gov/res/{urls[0]['href']}"
            detail_urls.append(details_url)

            try:
                arrest_date = datetime.strptime(intake, "%m/%d/%Y %H:%M").date()
            except ValueError:
                arrest_date = None

            basic_inmate_data.append(
                {
                    "name": name,
                    "race": race,
                    "sex": sex,
                    "arrest_date": arrest_date,
                }
            )
        else:
            logger.warning(f"No detail URL found for inmate: {name}")

    logger.info(f"Found {len(basic_inmate_data)} inmates to process")

    # Scrape detailed information
    if use_async and len(detail_urls) > 0:
        try:
            logger.info(
                f"Using async scraping with {max_concurrent} concurrent requests"
            )
            detailed_data = asyncio.run(
                async_scrape_all_inmate_details(detail_urls, max_concurrent)
            )
        except (RuntimeError, OSError, asyncio.TimeoutError) as e:
            logger.error(f"Async scraping failed, falling back to threading: {e}")
            detailed_data = scrape_with_threading(
                detail_urls, max_workers=min(5, len(detail_urls))
            )
    else:
        logger.info("Using threaded scraping")
        detailed_data = scrape_with_threading(
            detail_urls, max_workers=min(5, len(detail_urls))
        )

    # Process inmates in batches
    inmates: List[Inmate] = []
    successful_scrapes = 0

    for basic_data, details in zip(basic_inmate_data, detailed_data):
        if details is None:
            logger.warning(
                f"Skipping inmate {basic_data['name']} due to failed detail scraping"
            )
            continue

        inmate = Inmate(  # pylint: disable=unexpected-keyword-arg
            name=basic_data["name"],
            race=basic_data["race"],
            sex=basic_data["sex"],
            arrest_date=basic_data["arrest_date"],
            jail_id=jail.jail_id,
            is_juvenile=False,
            mugshot=details["mugshot"],
            held_for_agency=details["department"],
            hold_reasons=details["charges"],
            dob="Unknown",
            release_date="",
            in_custody_date=date.today(),
            hide_record=False,
        )
        inmates.append(inmate)
        successful_scrapes += 1

        logger.debug(
            f"Added inmate: {basic_data['name']} with arrest date: {basic_data['arrest_date']}"
        )

    end_time = time.time()
    scraping_time = end_time - start_time

    logger.success(
        f"Successfully scraped {successful_scrapes}/{len(basic_inmate_data)} inmates in {scraping_time:.2f} seconds"
    )
    logger.info(
        f"Average time per inmate: {scraping_time/len(basic_inmate_data):.2f} seconds"
    )

    # Process the scraped data
    process_start = time.time()
    process_scrape_data(session, inmates, jail)
    process_time = time.time() - process_start

    total_time = time.time() - start_time
    logger.info(
        f"Total processing time: {total_time:.2f} seconds (scraping: {scraping_time:.2f}s, processing: {process_time:.2f}s)"
    )


# Backward compatibility - use optimized version by default
def scrape_washington_so_ar(
    session: Session, jail: Jail, log_level: str = "INFO"
):  # pylint: disable=unused-argument
    """
    Backward compatible wrapper that uses the optimized scraper.

    Args:
        session (Session): SQLAlchemy session for database operations.
        jail (Jail): Jail object containing jail details.
        log_level (str): Legacy parameter for backward compatibility (unused).
    """
    return scrape_washington_so_ar_optimized(session, jail)
