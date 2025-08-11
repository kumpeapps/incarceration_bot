"""
Updated scraper example showing how to use the new optimized processing.
This replaces the old approach with the new deduplication logic.
"""

from datetime import datetime, date
from typing import List, Dict, Any
from loguru import logger
from models.Jail import Jail
from models.Monitor import Monitor
from database_connect import new_session
from processing_helper import save_inmates_optimized

def process_scrape_data_with_optimization(inmates_data: List[Dict[str, Any]], jail: Jail):
    """
    Process scraped inmate data using the new optimized approach.
    
    This function:
    1. Uses optimized processing to handle deduplication
    2. Updates monitors with last seen information
    3. Handles release date population automatically
    
    Args:
        inmates_data: List of inmate dictionaries from scraping
        jail: Jail object containing jail details
    """
    
    logger.info(f"Processing {jail.jail_name} with optimization - {len(inmates_data)} inmates")
    
    # Process inmates using optimized method
    stats = save_inmates_optimized(inmates_data, jail.jail_id)
    
    logger.info(f"Inmate processing complete: {stats}")
    
    # Update monitors separately (this logic remains similar)
    update_monitors_with_scraped_data(inmates_data, jail)
    
    logger.info(f"Completed processing for {jail.jail_name}")


def update_monitors_with_scraped_data(inmates_data: List[Dict[str, Any]], jail: Jail):
    """
    Update monitor records based on scraped inmate data.
    This maintains the existing monitor functionality.
    """
    
    with new_session() as session:
        try:
            # Pre-load all monitors
            monitors = session.query(Monitor).all()
            
            # Create lookup dictionaries
            monitor_by_exact_name: Dict[str, Monitor] = {}
            monitor_partial_matches: List[Monitor] = []
            
            for monitor in monitors:
                monitor_name = str(monitor.name)
                monitor_by_exact_name[monitor_name] = monitor
                monitor_partial_matches.append(monitor)
            
            monitors_to_update = []
            new_monitors = []
            current_time = datetime.now()
            
            # Process each inmate for monitor updates
            for inmate_data in inmates_data:
                inmate_name = inmate_data.get('name', '').strip()
                if not inmate_name:
                    continue
                
                # Check for exact monitor match
                monitor = monitor_by_exact_name.get(inmate_name)
                
                if monitor:
                    # Update existing monitor
                    monitor.last_seen_incarcerated = current_time
                    monitor.arrest_date = inmate_data.get('arrest_date', '')
                    monitor.release_date = inmate_data.get('release_date', '')
                    monitor.jail = jail.jail_name
                    monitors_to_update.append(monitor)
                else:
                    # Check for partial matches
                    for potential_monitor in monitor_partial_matches:
                        if _names_match(inmate_name, str(potential_monitor.name)):
                            potential_monitor.last_seen_incarcerated = current_time
                            potential_monitor.arrest_date = inmate_data.get('arrest_date', '')
                            potential_monitor.release_date = inmate_data.get('release_date', '')
                            potential_monitor.jail = jail.jail_name
                            monitors_to_update.append(potential_monitor)
                            break
            
            # Batch commit monitor updates
            if monitors_to_update or new_monitors:
                session.add_all(new_monitors)
                session.commit()
                logger.info(f"Updated {len(monitors_to_update)} monitors, created {len(new_monitors)} new monitors")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating monitors for {jail.jail_name}: {e}")


def _names_match(name1: str, name2: str) -> bool:
    """
    Check if two names match (handles various name format differences).
    This is the existing logic from the original processor.
    """
    
    # Remove common suffixes and prefixes
    suffixes = ["JR", "SR", "II", "III", "IV"]
    
    def clean_name(name: str) -> str:
        name = name.upper().strip()
        # Remove punctuation and extra spaces
        name = "".join(c if c.isalnum() or c.isspace() else " " for c in name)
        name = " ".join(name.split())
        
        # Remove suffixes
        for suffix in suffixes:
            if name.endswith(f" {suffix}"):
                name = name[: -(len(suffix) + 1)]
                break
        
        return name
    
    cleaned_name1 = clean_name(name1)
    cleaned_name2 = clean_name(name2)
    
    if cleaned_name1 == cleaned_name2:
        return True
    
    # Check if names are contained within each other (partial match)
    words1 = set(cleaned_name1.split())
    words2 = set(cleaned_name2.split())
    
    # Names match if they share at least 2 words and one is a subset of the other
    common_words = words1.intersection(words2)
    if len(common_words) >= 2 and (words1.issubset(words2) or words2.issubset(words1)):
        return True
    
    return False


# Example of how to update existing scrapers:
def example_scraper_integration():
    """
    Example showing how to update an existing scraper to use the new approach.
    
    OLD WAY:
    ```python
    # Create Inmate objects
    inmates = []
    for data in scraped_data:
        inmate = Inmate(**data)
        inmates.append(inmate)
    
    # Process with old method
    process_scrape_data_optimized(session, inmates, jail)
    ```
    
    NEW WAY:
    ```python
    # Keep data as dictionaries, use optimized processing
    process_scrape_data_with_optimization(scraped_data, jail)
    ```
    """
    pass


def migrate_jail_to_new_system(jail_id: str):
    """
    One-time migration function to clean up a specific jail's data
    and prepare it for the new optimized processing.
    """
    from processing_helper import migrate_jail_data
    
    logger.info(f"Migrating jail {jail_id} to optimized system")
    
    # Clean up duplicates
    stats = migrate_jail_data(jail_id)
    
    logger.info(f"Migration complete for {jail_id}: {stats}")
    return stats
