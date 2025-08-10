"""
Integration helper to easily switch existing scrapers to use optimized processing.
"""

from typing import List, Dict, Any, Optional
import logging
from optimized_processing import process_jail_optimized

logger = logging.getLogger(__name__)

def save_inmates_optimized(inmates_data: List[Dict[str, Any]], jail_id: str) -> Dict[str, int]:
    """
    Drop-in replacement for existing save_inmates functions.
    Uses optimized processing to handle deduplication and efficiency.
    
    Args:
        inmates_data: List of inmate dictionaries from scraping
        jail_id: The jail identifier
        
    Returns:
        Dictionary with processing statistics
    """
    
    if not inmates_data:
        logger.warning(f"No inmates data provided for jail {jail_id}")
        return {'updated': 0, 'new': 0, 'released': 0, 'errors': 0}
    
    logger.info(f"Processing {len(inmates_data)} inmates for jail {jail_id} using optimized method")
    
    try:
        stats = process_jail_optimized(jail_id, inmates_data)
        logger.info(f"Jail {jail_id} processed: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error in optimized processing for jail {jail_id}: {e}")
        return {'updated': 0, 'new': 0, 'released': 0, 'errors': len(inmates_data)}


def migrate_jail_data(jail_id: Optional[str] = None) -> Dict[str, int]:
    """
    Migrate existing jail data to remove duplicates.
    
    Args:
        jail_id: Optional specific jail ID, if None processes all jails
        
    Returns:
        Migration statistics
    """
    from optimized_processing import migrate_existing_data
    
    logger.info(f"Starting data migration for jail {jail_id or 'ALL JAILS'}")
    return migrate_existing_data(jail_id)
