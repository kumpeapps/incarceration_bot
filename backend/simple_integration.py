"""
Simple integration module for existing scrapers to use optimized processing.
This provides drop-in replacements for existing functions.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def process_inmates_optimized(inmates_data: List[Dict[str, Any]], jail_id: str) -> Dict[str, int]:
    """
    Drop-in replacement for existing inmate processing functions.
    
    Args:
        inmates_data: List of inmate dictionaries (not Inmate objects)
        jail_id: Jail identifier string
        
    Returns:
        Dictionary with processing statistics
    """
    from optimized_processing import OptimizedInmateProcessor
    
    if not inmates_data:
        logger.warning(f"No inmates data provided for jail {jail_id}")
        return {'updated': 0, 'new': 0, 'released': 0, 'errors': 0}
    
    logger.info(f"Processing {len(inmates_data)} inmates for jail {jail_id} (optimized)")
    
    try:
        with OptimizedInmateProcessor() as processor:
            return processor.process_jail_inmates(jail_id, inmates_data)
    except Exception as e:
        logger.error(f"Optimized processing failed for jail {jail_id}: {e}")
        return {'updated': 0, 'new': 0, 'released': 0, 'errors': len(inmates_data)}

def convert_inmate_objects_to_dicts(inmate_objects) -> List[Dict[str, Any]]:
    """
    Convert Inmate objects to dictionaries for use with optimized processing.
    
    Args:
        inmate_objects: List of Inmate objects
        
    Returns:
        List of dictionaries
    """
    result = []
    
    for inmate in inmate_objects:
        if hasattr(inmate, 'to_dict'):
            # Use the object's to_dict method if available
            result.append(inmate.to_dict())
        else:
            # Manual conversion
            inmate_dict = {
                'name': getattr(inmate, 'name', ''),
                'race': getattr(inmate, 'race', 'Unknown'),
                'sex': getattr(inmate, 'sex', 'Unknown'),
                'cell_block': getattr(inmate, 'cell_block', ''),
                'arrest_date': getattr(inmate, 'arrest_date', None),
                'held_for_agency': getattr(inmate, 'held_for_agency', ''),
                'mugshot': getattr(inmate, 'mugshot', ''),
                'dob': getattr(inmate, 'dob', 'Unknown'),
                'hold_reasons': getattr(inmate, 'hold_reasons', ''),
                'is_juvenile': getattr(inmate, 'is_juvenile', False),
                'release_date': getattr(inmate, 'release_date', ''),
                'hide_record': getattr(inmate, 'hide_record', False),
            }
            result.append(inmate_dict)
    
    return result

def migrate_to_optimized_processing(jail_id: Optional[str] = None) -> Dict[str, int]:
    """
    One-time migration to prepare existing data for optimized processing.
    
    Args:
        jail_id: Optional jail ID, if None processes all jails
        
    Returns:
        Migration statistics
    """
    from optimized_processing import migrate_existing_data
    
    logger.info(f"Running migration for jail {jail_id or 'ALL'}")
    return migrate_existing_data(jail_id)

# Example usage for updating existing scrapers:
"""
OLD CODE:
```python
def some_scraper():
    # ... scraping logic ...
    
    inmates = []
    for data in scraped_data:
        inmate = Inmate(**data)
        inmates.append(inmate)
    
    process_scrape_data_optimized(session, inmates, jail)
```

NEW CODE:
```python
def some_scraper():
    # ... scraping logic ...
    
    # Keep as dictionaries, no need to create Inmate objects
    from simple_integration import process_inmates_optimized
    
    stats = process_inmates_optimized(scraped_data, jail.jail_id)
    logger.info(f"Processing stats: {stats}")
```

MIGRATION FROM EXISTING CODE:
```python
def some_scraper():
    # ... scraping logic ...
    
    # If you already have Inmate objects:
    inmates = [Inmate(**data) for data in scraped_data]
    
    # Convert to dicts and use optimized processing
    from simple_integration import convert_inmate_objects_to_dicts, process_inmates_optimized
    
    inmate_dicts = convert_inmate_objects_to_dicts(inmates)
    stats = process_inmates_optimized(inmate_dicts, jail.jail_id)
```
"""
