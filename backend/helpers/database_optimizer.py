"""
Optimized Database Operations for Binlog Reduction

This module contains optimizations to reduce MariaDB binlog bloat by:
1. Only updating last_seen when significantly different (>1 hour)
2. Batching database operations
3. Reducing unnecessary timestamp updates
4. Using more efficient upsert operations
"""

from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from loguru import logger


class DatabaseOptimizer:
    """Optimized database operations to reduce binlog writes."""
    
    # Only update last_seen if more than 1 hour has passed
    LAST_SEEN_UPDATE_THRESHOLD = timedelta(hours=1)
    
    @staticmethod
    def optimized_upsert_inmate(session: Session, inmate_data: dict, auto_commit: bool = False):
        """
        Optimized inmate upsert that only updates last_seen if significantly different.
        Reduces binlog bloat by avoiding unnecessary timestamp updates.
        """
        engine = session.get_bind()
        if engine.dialect.name == "mysql":
            # Only update last_seen if it's been more than 1 hour since last update
            sql = text("""
                INSERT INTO inmates (
                    name, race, sex, cell_block, arrest_date, held_for_agency, 
                    mugshot, dob, hold_reasons, is_juvenile, release_date, 
                    in_custody_date, jail_id, hide_record, last_seen
                ) VALUES (
                    :name, :race, :sex, :cell_block, :arrest_date, :held_for_agency,
                    :mugshot, :dob, :hold_reasons, :is_juvenile, :release_date,
                    :in_custody_date, :jail_id, :hide_record, :last_seen
                )
                ON DUPLICATE KEY UPDATE
                    -- Only update if last_seen is NULL or more than 1 hour old
                    last_seen = CASE 
                        WHEN last_seen IS NULL OR last_seen < DATE_SUB(NOW(), INTERVAL 1 HOUR)
                        THEN VALUES(last_seen)
                        ELSE last_seen
                    END,
                    -- Always update these fields as they may have changed
                    cell_block = VALUES(cell_block),
                    arrest_date = VALUES(arrest_date),
                    held_for_agency = VALUES(held_for_agency),
                    mugshot = VALUES(mugshot),
                    in_custody_date = VALUES(in_custody_date),
                    release_date = VALUES(release_date),
                    hold_reasons = VALUES(hold_reasons)
            """)
            
            # Ensure last_seen is set to current time for new records
            if 'last_seen' not in inmate_data or inmate_data['last_seen'] is None:
                inmate_data['last_seen'] = datetime.now()
                
            session.execute(sql, inmate_data)
        else:
            # Fallback for non-MySQL databases
            from helpers.insert_ignore import insert_ignore
            insert_ignore(session, model=None, values=inmate_data, auto_commit=False)
        
        if auto_commit:
            session.commit()
    
    @staticmethod
    def batch_upsert_inmates(session: Session, inmates_data: list[dict], batch_size: int = 100):
        """
        Batch upsert inmates to reduce the number of database round trips.
        
        Args:
            session: SQLAlchemy session
            inmates_data: List of inmate dictionaries
            batch_size: Number of records to process in each batch
        """
        engine = session.get_bind()
        if engine.dialect.name != "mysql":
            # Fall back to individual operations for non-MySQL
            for inmate_data in inmates_data:
                DatabaseOptimizer.optimized_upsert_inmate(session, inmate_data, auto_commit=False)
            session.commit()
            return
        
        logger.info(f"Batch upserting {len(inmates_data)} inmates in batches of {batch_size}")
        
        # Process in batches
        for i in range(0, len(inmates_data), batch_size):
            batch = inmates_data[i:i + batch_size]
            
            # Build VALUES clause for batch insert
            values_clauses = []
            params = {}
            
            for j, inmate_data in enumerate(batch):
                # Create unique parameter names for this batch item
                param_names = {key: f"{key}_{j}" for key in inmate_data.keys()}
                
                # Add parameters to the params dict
                for key, value in inmate_data.items():
                    params[param_names[key]] = value
                
                # Ensure last_seen is set
                if f'last_seen_{j}' not in params or params[f'last_seen_{j}'] is None:
                    params[f'last_seen_{j}'] = datetime.now()
                
                # Build the VALUES clause for this record
                value_clause = f"(:{param_names['name']}, :{param_names['race']}, :{param_names['sex']}, :{param_names['cell_block']}, :{param_names['arrest_date']}, :{param_names['held_for_agency']}, :{param_names['mugshot']}, :{param_names['dob']}, :{param_names['hold_reasons']}, :{param_names['is_juvenile']}, :{param_names['release_date']}, :{param_names['in_custody_date']}, :{param_names['jail_id']}, :{param_names['hide_record']}, :{param_names['last_seen']})"
                values_clauses.append(value_clause)
            
            # Execute batch insert
            sql = text(f"""
                INSERT INTO inmates (
                    name, race, sex, cell_block, arrest_date, held_for_agency, 
                    mugshot, dob, hold_reasons, is_juvenile, release_date, 
                    in_custody_date, jail_id, hide_record, last_seen
                ) VALUES {', '.join(values_clauses)}
                ON DUPLICATE KEY UPDATE
                    last_seen = CASE 
                        WHEN last_seen IS NULL OR last_seen < DATE_SUB(NOW(), INTERVAL 1 HOUR)
                        THEN VALUES(last_seen)
                        ELSE last_seen
                    END,
                    cell_block = VALUES(cell_block),
                    arrest_date = VALUES(arrest_date),
                    held_for_agency = VALUES(held_for_agency),
                    mugshot = VALUES(mugshot),
                    in_custody_date = VALUES(in_custody_date),
                    release_date = VALUES(release_date),
                    hold_reasons = VALUES(hold_reasons)
            """)
            
            try:
                session.execute(sql, params)
                logger.debug(f"Successfully processed batch {i//batch_size + 1}")
            except Exception as e:
                logger.error(f"Error in batch {i//batch_size + 1}: {e}")
                # Fall back to individual inserts for this batch
                for inmate_data in batch:
                    try:
                        DatabaseOptimizer.optimized_upsert_inmate(session, inmate_data, auto_commit=False)
                    except Exception as individual_error:
                        logger.error(f"Failed to insert individual inmate: {individual_error}")
        
        # Commit all batches at once
        session.commit()
        logger.info(f"Completed batch upsert of {len(inmates_data)} inmates")
    
    @staticmethod
    def optimize_monitor_updates(session: Session, monitor_updates: list[tuple], batch_size: int = 50):
        """
        Batch update monitors to reduce database writes.
        
        Args:
            session: SQLAlchemy session
            monitor_updates: List of (monitor_id, last_seen_incarcerated) tuples
            batch_size: Number of updates per batch
        """
        if not monitor_updates:
            return
        
        logger.info(f"Batch updating {len(monitor_updates)} monitors")
        
        # Process in batches
        for i in range(0, len(monitor_updates), batch_size):
            batch = monitor_updates[i:i + batch_size]
            
            # Build CASE statement for batch update
            when_clauses = []
            monitor_ids = []
            params = {}
            
            for j, (monitor_id, last_seen) in enumerate(batch):
                when_clauses.append(f"WHEN id = :monitor_id_{j} THEN :last_seen_{j}")
                params[f'monitor_id_{j}'] = monitor_id
                params[f'last_seen_{j}'] = last_seen
                monitor_ids.append(f":monitor_id_{j}")
            
            sql = text(f"""
                UPDATE monitors 
                SET last_seen_incarcerated = CASE 
                    {' '.join(when_clauses)}
                    ELSE last_seen_incarcerated
                END
                WHERE id IN ({', '.join(monitor_ids)})
                AND (last_seen_incarcerated IS NULL OR last_seen_incarcerated < DATE_SUB(NOW(), INTERVAL 1 HOUR))
            """)
            
            session.execute(sql, params)
        
        session.commit()
        logger.debug(f"Completed batch update of {len(monitor_updates)} monitors")


# Helper function to check if last_seen needs updating
def should_update_last_seen(current_last_seen: Optional[datetime], threshold_hours: int = 1) -> bool:
    """
    Check if last_seen timestamp should be updated based on threshold.
    
    Args:
        current_last_seen: Current last_seen timestamp
        threshold_hours: Minimum hours between updates
        
    Returns:
        True if last_seen should be updated
    """
    if current_last_seen is None:
        return True
    
    threshold = timedelta(hours=threshold_hours)
    return datetime.now() - current_last_seen > threshold