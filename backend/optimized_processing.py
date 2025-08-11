"""
Optimized inmate processing to reduce data duplication and improve efficiency.
This module handles:
1. Deduplication by jail + arrest_date 
2. Updating existing records (charges, mugshot, last_seen)
3. Auto-populating release_dates when inmates disappear
4. Handling gaps in custody as separate incarcerations
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, text
from models.Inmate import Inmate
from database_connect import new_session
import logging

logger = logging.getLogger(__name__)

class OptimizedInmateProcessor:
    """Handles optimized inmate data processing to reduce duplication."""
    
    def __init__(self):
        self.session = new_session()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()
    
    def process_jail_inmates(self, jail_id: str, scraped_inmates: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Process a list of scraped inmates for a specific jail efficiently.
        
        Args:
            jail_id: The jail identifier
            scraped_inmates: List of inmate dictionaries from scraping
            
        Returns:
            Dictionary with counts of updated, new, and released inmates
        """
        current_time = datetime.now()
        current_date = current_time.date()
        
        stats = {
            'updated': 0,
            'new': 0,
            'released': 0,
            'errors': 0
        }
        
        try:
            # Get all currently active inmates for this jail (no release date)
            existing_inmates = self.session.query(Inmate).filter(
                and_(
                    Inmate.jail_id == jail_id,
                    or_(Inmate.release_date == "", Inmate.release_date.is_(None))
                )
            ).all()
            
            # Create lookup maps for efficient searching
            existing_by_key = {}
            existing_names = set()
            
            for inmate in existing_inmates:
                # Primary key: name + arrest_date
                key = f"{inmate.name}|{inmate.arrest_date}"
                existing_by_key[key] = inmate
                existing_names.add(inmate.name)
            
            # Track which inmates we've seen in this scrape
            seen_inmates: Set[str] = set()
            
            # Process each scraped inmate
            for scraped_data in scraped_inmates:
                try:
                    processed = self._process_single_inmate(
                        scraped_data, jail_id, current_time, 
                        existing_by_key, seen_inmates
                    )
                    
                    if processed == 'updated':
                        stats['updated'] += 1
                    elif processed == 'new':
                        stats['new'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing inmate {scraped_data.get('name', 'Unknown')}: {e}")
                    stats['errors'] += 1
            
            # Mark inmates as released if they weren't found in this scrape
            released_count = self._mark_missing_as_released(
                existing_inmates, seen_inmates, current_date
            )
            stats['released'] = released_count
            
            # Commit all changes
            self.session.commit()
            
            logger.info(f"Jail {jail_id} processing complete: {stats}")
            return stats
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error processing jail {jail_id}: {e}")
            stats['errors'] += len(scraped_inmates)
            return stats
    
    def _process_single_inmate(self, scraped_data: Dict[str, Any], jail_id: str, 
                              current_time: datetime, existing_by_key: Dict[str, Inmate],
                              seen_inmates: set) -> str:
        """Process a single inmate record."""
        
        name = scraped_data.get('name', '').strip()
        if not name:
            raise ValueError("Inmate name is required")
        
        # Parse arrest date
        arrest_date = self._parse_date(scraped_data.get('arrest_date'))
        if not arrest_date:
            arrest_date = current_time.date()
        
        # Create lookup key
        key = f"{name}|{arrest_date}"
        seen_inmates.add(name)
        
        # Check if inmate already exists with same arrest date
        if key in existing_by_key:
            return self._update_existing_inmate(existing_by_key[key], scraped_data, current_time)
        else:
            # Check for gaps in custody (same name, different arrest date)
            return self._create_or_reactivate_inmate(scraped_data, jail_id, current_time, arrest_date)
    
    def _update_existing_inmate(self, existing_inmate: Inmate, scraped_data: Dict[str, Any], 
                               current_time: datetime) -> str:
        """Update an existing inmate record with new information."""
        
        updated = False
        
        # Update fields that might change
        if scraped_data.get('hold_reasons') and scraped_data['hold_reasons'] != existing_inmate.hold_reasons:
            existing_inmate.hold_reasons = scraped_data['hold_reasons']
            updated = True
        
        if scraped_data.get('mugshot') and scraped_data['mugshot'] != existing_inmate.mugshot:
            existing_inmate.mugshot = scraped_data['mugshot']
            updated = True
        
        if scraped_data.get('cell_block') and scraped_data['cell_block'] != existing_inmate.cell_block:
            existing_inmate.cell_block = scraped_data['cell_block']
            updated = True
        
        # Always update last_seen
        existing_inmate.last_seen = current_time
        
        # Clear release date if it was set (inmate is back in custody)
        if existing_inmate.release_date:
            existing_inmate.release_date = ""
            updated = True
        
        return 'updated' if updated else 'seen'
    
    def _create_or_reactivate_inmate(self, scraped_data: Dict[str, Any], jail_id: str,
                                   current_time: datetime, arrest_date: date) -> str:
        """Create a new inmate record or reactivate if this is a re-booking."""
        
        # Check if this person has been here before with a different arrest date
        name = scraped_data.get('name', '').strip()
        previous_bookings = self.session.query(Inmate).filter(
            and_(
                Inmate.jail_id == jail_id,
                Inmate.name == name,
                Inmate.arrest_date != arrest_date
            )
        ).order_by(desc(Inmate.arrest_date)).all()
        
        # If there are previous bookings, ensure the most recent one is marked as released
        if previous_bookings:
            latest_booking = previous_bookings[0]
            if not latest_booking.release_date or latest_booking.release_date == "":
                # Mark previous booking as released (gap in custody)
                latest_booking.release_date = (arrest_date - timedelta(days=1)).isoformat()
        
        # Create new inmate record
        new_inmate = Inmate(
            name=name,
            race=scraped_data.get('race', 'Unknown'),
            sex=scraped_data.get('sex', 'Unknown'),
            cell_block=scraped_data.get('cell_block', ''),
            arrest_date=arrest_date,
            held_for_agency=scraped_data.get('held_for_agency', ''),
            mugshot=scraped_data.get('mugshot', ''),
            dob=scraped_data.get('dob', 'Unknown'),
            hold_reasons=scraped_data.get('hold_reasons', ''),
            is_juvenile=scraped_data.get('is_juvenile', False),
            release_date="",
            in_custody_date=current_time.date(),
            last_seen=current_time,
            jail_id=jail_id,
            hide_record=scraped_data.get('hide_record', False)
        )
        
        self.session.add(new_inmate)
        return 'new'
    
    def _mark_missing_as_released(self, existing_inmates: List[Inmate], 
                                 seen_inmates: set, current_date: date) -> int:
        """Mark inmates as released if they weren't found in the current scrape."""
        
        released_count = 0
        
        for inmate in existing_inmates:
            if inmate.name not in seen_inmates:
                # Inmate not found in current scrape, mark as released
                if not inmate.release_date or inmate.release_date == "":
                    inmate.release_date = current_date.isoformat()
                    released_count += 1
        
        return released_count
    
    def _parse_date(self, date_str: Any) -> Optional[date]:
        """Parse various date formats into a date object."""
        if not date_str:
            return None
        
        if isinstance(date_str, date):
            return date_str
        
        if isinstance(date_str, datetime):
            return date_str.date()
        
        if isinstance(date_str, str):
            # Try common date formats
            formats = ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d']
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
        
        return None
    
    def cleanup_duplicate_records(self, jail_id: Optional[str] = None) -> int:
        """
        Clean up duplicate records that may exist from before optimization.
        This is intended for one-time migration use.
        """
        
        where_clause = ""
        if jail_id:
            where_clause = f"WHERE jail_id = '{jail_id}'"
        
        # Find and remove duplicates, keeping the most recent record
        cleanup_sql = f"""
        DELETE i1 FROM inmates i1
        INNER JOIN inmates i2 
        WHERE i1.id < i2.id 
        AND i1.name = i2.name 
        AND i1.jail_id = i2.jail_id 
        AND i1.arrest_date = i2.arrest_date
        {where_clause}
        """
        
        result = self.session.execute(text(cleanup_sql))
        deleted_count = result.rowcount
        self.session.commit()
        
        logger.info(f"Cleaned up {deleted_count} duplicate records for jail {jail_id or 'all jails'}")
        return deleted_count


def process_jail_optimized(jail_id: str, scraped_inmates: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Main function to process inmates for a jail using the optimized approach.
    
    Args:
        jail_id: Jail identifier
        scraped_inmates: List of scraped inmate data
        
    Returns:
        Processing statistics
    """
    with OptimizedInmateProcessor() as processor:
        return processor.process_jail_inmates(jail_id, scraped_inmates)


def migrate_existing_data(jail_id: Optional[str] = None) -> Dict[str, int]:
    """
    One-time migration function to clean up existing duplicate data.
    
    Args:
        jail_id: Optional jail to migrate, if None migrates all jails
        
    Returns:
        Migration statistics
    """
    with OptimizedInmateProcessor() as processor:
        deleted = processor.cleanup_duplicate_records(jail_id)
        return {'duplicates_removed': deleted}
