"""
Shared utilities for jail scraping operations
Provides common functions used across different scraper modules
"""

import re
from datetime import datetime
from typing import Optional
from loguru import logger


def parse_date_flexible(date_raw: any, field_name: str = "date") -> str:
    """
    Parse date from various formats into standardized string format.
    This function can be used for arrest_date, release_date, or any other date field.
    
    Args:
        date_raw: Raw date from API (could be various formats)
        field_name: Name of the field being parsed (for logging)
        
    Returns:
        str: Formatted date string (YYYY-MM-DD) or empty string if invalid/missing
    """
    if not date_raw or date_raw in ['', 'None', 'null', 'TBD', 'Unknown', 'N/A']:
        return ""
    
    # Convert to string and clean up
    date_str = str(date_raw).strip()
    
    if not date_str:
        return ""
    
    # Remove timezone info if present (e.g., 2025-09-04T15:30:00.000Z)
    if 'T' in date_str and ('Z' in date_str or '+' in date_str or '-' in date_str[-6:]):
        # Extract just the date part before timezone
        date_str = date_str.split('T')[0]
    
    # Remove common prefixes/suffixes that might interfere
    date_str = re.sub(r'^(Date:\s*|Released:\s*|Arrested:\s*)', '', date_str, flags=re.IGNORECASE)
    date_str = re.sub(r'\s*(EST|PST|CST|MST|EDT|PDT|CDT|MDT)$', '', date_str, flags=re.IGNORECASE)
    
    # Try different date formats that jail systems might return
    date_formats = [
        "%Y-%m-%d",           # 2025-09-04 (ISO standard)
        "%Y-%m-%dT%H:%M:%S",  # 2025-09-04T10:30:00 (ISO with time)
        "%Y-%m-%d %H:%M:%S",  # 2025-09-04 10:30:00 (Date with time)
        "%m/%d/%Y",           # 09/04/2025 (US format)
        "%m-%d-%Y",           # 09-04-2025 (US format with dashes)
        "%d/%m/%Y",           # 04/09/2025 (European format)
        "%d-%m-%Y",           # 04-09-2025 (European format with dashes)
        "%Y-%m-%d %H:%M",     # 2025-09-04 10:30 (Date with hours:minutes)
        "%m/%d/%Y %H:%M:%S",  # 09/04/2025 10:30:00 (US format with time)
        "%m/%d/%Y %H:%M",     # 09/04/2025 10:30 (US format with hours:minutes)
        "%m/%d/%y",           # 09/04/25 (US format 2-digit year)
        "%d/%m/%y",           # 04/09/25 (European format 2-digit year)
        "%Y%m%d",             # 20250904 (Compact format)
        "%m%d%Y",             # 09042025 (US compact format)
        "%d%m%Y",             # 04092025 (European compact format)
        "%B %d, %Y",          # September 4, 2025 (Full month name)
        "%b %d, %Y",          # Sep 4, 2025 (Abbreviated month name)
        "%d %B %Y",           # 4 September 2025 (European full month)
        "%d %b %Y",           # 4 Sep 2025 (European abbreviated month)
    ]
    
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, date_format).date()
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # If no format matches, log warning and return empty
    logger.warning(f"Could not parse {field_name}: {date_raw}")
    return ""


def parse_arrest_date(arrest_date_raw: any) -> Optional[datetime.date]:
    """
    Parse arrest date into a date object.
    
    Args:
        arrest_date_raw: Raw arrest date from API
        
    Returns:
        date object or None if invalid/missing
    """
    date_str = parse_date_flexible(arrest_date_raw, "arrest_date")
    if not date_str:
        return None
    
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_release_date(release_date_raw: any) -> str:
    """
    Parse release date into a standardized string format.
    
    Args:
        release_date_raw: Raw release date from API
        
    Returns:
        str: Formatted date string (YYYY-MM-DD) or empty string if invalid/missing
    """
    return parse_date_flexible(release_date_raw, "release_date")


def clean_text_field(text_raw: any, max_length: Optional[int] = None) -> str:
    """
    Clean and standardize text fields from scraping.
    
    Args:
        text_raw: Raw text from API
        max_length: Maximum length to truncate to
        
    Returns:
        str: Cleaned text or empty string
    """
    if not text_raw or text_raw in ['', 'None', 'null', 'N/A', 'Unknown']:
        return ""
    
    # Convert to string and clean up
    text = str(text_raw).strip()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common unwanted characters
    text = re.sub(r'[^\w\s\-\.\,\(\)\:\;]', '', text)
    
    # Truncate if necessary
    if max_length and len(text) > max_length:
        text = text[:max_length-3] + "..."
    
    return text


def standardize_boolean(bool_raw: any) -> bool:
    """
    Standardize boolean values from various formats.
    
    Args:
        bool_raw: Raw boolean value from API
        
    Returns:
        bool: Standardized boolean value
    """
    if isinstance(bool_raw, bool):
        return bool_raw
    
    if isinstance(bool_raw, (int, float)):
        return bool(bool_raw)
    
    if isinstance(bool_raw, str):
        bool_str = bool_raw.lower().strip()
        if bool_str in ['true', 'yes', 'y', '1', 'on', 'active']:
            return True
        elif bool_str in ['false', 'no', 'n', '0', 'off', 'inactive']:
            return False
    
    # Default to False for unknown values
    return False


def validate_scrape_data(inmate_data: dict) -> dict:
    """
    Validate and clean scraped inmate data.
    
    Args:
        inmate_data: Dictionary of inmate data from scraping
        
    Returns:
        dict: Validated and cleaned inmate data
    """
    validated = {}
    
    # Required fields
    validated['name'] = clean_text_field(inmate_data.get('name', ''), max_length=255)
    
    # Date fields
    validated['arrest_date'] = parse_arrest_date(inmate_data.get('arrest_date'))
    validated['release_date'] = parse_release_date(inmate_data.get('release_date'))
    
    # Text fields with length limits
    validated['hold_reasons'] = clean_text_field(inmate_data.get('hold_reasons', ''))
    validated['held_for_agency'] = clean_text_field(inmate_data.get('held_for_agency', ''), max_length=255)
    validated['race'] = clean_text_field(inmate_data.get('race', ''), max_length=50)
    validated['sex'] = clean_text_field(inmate_data.get('sex', ''), max_length=10)
    validated['cell_block'] = clean_text_field(inmate_data.get('cell_block', ''), max_length=100)
    validated['dob'] = clean_text_field(inmate_data.get('dob', 'Unknown'), max_length=50)
    
    # Boolean fields
    validated['is_juvenile'] = standardize_boolean(inmate_data.get('is_juvenile', False))
    validated['hide_record'] = standardize_boolean(inmate_data.get('hide_record', False))
    
    # Special fields
    validated['mugshot'] = inmate_data.get('mugshot', '')  # Keep as-is for now
    validated['jail_id'] = inmate_data.get('jail_id', '')
    
    return validated
