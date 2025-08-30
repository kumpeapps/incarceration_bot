"""
Optimized Database Operations for Binlog Reduction

This module contains optimizations to reduce MariaDB binlog bloat by:
1. Only updating last_seen when significantly different (>1 hour)
2. Batching database operations
3. Reducing unnecessary timestamp updates
4. Using more efficient upsert operations
"""

import time
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, DisconnectionError
from typing import Dict, Any, Optional
from loguru import logger


class DatabaseOptimizer:
    """Optimized database operations to reduce binlog writes."""
    
    @staticmethod
    def validate_connection(session: Session) -> bool:
        """Validate that the database connection is still active."""
        try:
            session.execute(text("SELECT 1"))
            return True
        except (OperationalError, DisconnectionError) as e:
            logger.warning(f"Database connection validation failed: {e}")
            return False
    
    @staticmethod
    def get_fresh_session(old_session: Session) -> Session:
        """Get a fresh database session, closing the old one if needed."""
        try:
            old_session.close()
        except Exception as e:
            logger.warning(f"Error closing old session: {e}")
        
        from database_connect import new_session
        new_sess = new_session()
        
        # Configure timeouts for the new session
        DatabaseOptimizer.configure_session_timeouts(new_sess)
        
        logger.info("Created fresh database session with configured timeouts")
        return new_sess
    
    @staticmethod
    def configure_session_timeouts(session: Session):
        """Configure MySQL session-level timeouts for batch operations."""
        try:
            # Set longer timeouts for this session
            session.execute(text("SET SESSION wait_timeout = 3600"))  # 1 hour
            session.execute(text("SET SESSION interactive_timeout = 3600"))  # 1 hour
            session.execute(text("SET SESSION net_read_timeout = 300"))  # 5 minutes
            session.execute(text("SET SESSION net_write_timeout = 300"))  # 5 minutes
            session.execute(text("SET SESSION innodb_lock_wait_timeout = 120"))  # 2 minutes for lock waits
            session.execute(text("SET SESSION transaction_isolation = 'READ-COMMITTED'"))  # Reduce lock contention
            logger.debug("Configured session timeouts for batch processing")
        except Exception as e:
            logger.warning(f"Could not configure session timeouts: {e}")
            # Not critical, continue without timeout changes
    
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
    def batch_upsert_inmates(session: Session, inmates_data: list[dict], batch_size: int = 50):
        """
        Batch upsert inmates to reduce the number of database round trips.
        
        Args:
            session: SQLAlchemy session
            inmates_data: List of inmate dictionaries
            batch_size: Number of records to process in each batch (reduced default for stability)
        """
        engine = session.get_bind()
        if engine.dialect.name != "mysql":
            # Fall back to individual operations for non-MySQL
            for inmate_data in inmates_data:
                DatabaseOptimizer.optimized_upsert_inmate(session, inmate_data, auto_commit=False)
            session.commit()
            return
        
        logger.info(f"Batch upserting {len(inmates_data)} inmates in batches of {batch_size}")
        
        # Validate connection before starting
        if not DatabaseOptimizer.validate_connection(session):
            logger.warning("Database connection invalid, creating fresh session")
            session = DatabaseOptimizer.get_fresh_session(session)
        
        # Configure session timeouts for batch processing
        DatabaseOptimizer.configure_session_timeouts(session)
        
        # Process in batches with connection validation
        batch_success_count = 0
        for i in range(0, len(inmates_data), batch_size):
            batch = inmates_data[i:i + batch_size]
            batch_num = i//batch_size + 1
            
            # Validate connection before each batch
            if not DatabaseOptimizer.validate_connection(session):
                logger.warning(f"Connection lost before batch {batch_num}, reconnecting")
                session = DatabaseOptimizer.get_fresh_session(session)
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
        
        # Build the SQL statement for this batch
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
        
        # Execute batch insert with retry logic
        batch_success = False
        retry_count = 0
        max_retries = 3
        
        while not batch_success and retry_count < max_retries:
            try:
                session.execute(sql, params)
                batch_success = True
                batch_success_count += 1
                logger.debug(f"Successfully processed batch {batch_num}")
                break
            except (OperationalError, DisconnectionError) as e:
                retry_count += 1
                logger.error(f"Connection error in batch {batch_num} (attempt {retry_count}/{max_retries}): {e}")
                
                # Roll back and get fresh connection
                try:
                    session.rollback()
                except:
                    pass
                
                if retry_count < max_retries:
                    session = DatabaseOptimizer.get_fresh_session(session)
                    time.sleep(min(2 ** retry_count, 10))  # Exponential backoff, max 10 seconds
                else:
                    logger.error(f"Max retries reached for batch {batch_num}, falling back to individual inserts")
                    break
            except Exception as e:
                retry_count += 1
                logger.error(f"Error in batch {batch_num} (attempt {retry_count}/{max_retries}): {e}")
                
                try:
                    session.rollback()
                except:
                    pass
                    
                if retry_count >= max_retries:
                    logger.error(f"Max retries reached for batch {batch_num}, falling back to individual inserts")
                    break
                
                time.sleep(min(2 ** retry_count, 10))  # Exponential backoff
        
        # If batch failed completely, fall back to individual inserts
        if not batch_success:
            logger.warning(f"Batch {batch_num} failed, processing {len(batch)} inmates individually")
            for inmate_data in batch:
                individual_success = False
                individual_retry_count = 0
                max_individual_retries = 2
                
                while not individual_success and individual_retry_count < max_individual_retries:
                    try:
                        # Validate connection before individual insert
                        if not DatabaseOptimizer.validate_connection(session):
                            session = DatabaseOptimizer.get_fresh_session(session)
                        
                        DatabaseOptimizer.optimized_upsert_inmate(session, inmate_data, auto_commit=False)
                        individual_success = True
                    except Exception as individual_error:
                        individual_retry_count += 1
                        logger.error(f"Failed to insert individual inmate (attempt {individual_retry_count}/{max_individual_retries}): {individual_error}")
                        
                        if "Lost connection" in str(individual_error) or "Can't reconnect" in str(individual_error):
                            # Connection lost, create new session
                            session = DatabaseOptimizer.get_fresh_session(session)
                        elif individual_retry_count < max_individual_retries:
                            # Other error, rollback and retry
                            try:
                                session.rollback()
                            except:
                                pass
                            time.sleep(1)  # Brief pause before retry
                        else:
                            # Max retries reached, log and continue
                            logger.error(f"Failed to insert inmate after {max_individual_retries} attempts: {inmate_data.get('name', 'unknown')}")
        
        # Commit all successful batches
        try:
            session.commit()
            logger.info(f"Completed batch upsert of {len(inmates_data)} inmates ({batch_success_count} successful batches)")
        except Exception as commit_error:
            logger.error(f"Error during final commit: {commit_error}")
            session.rollback()
            raise
    
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
            
            for monitor_id, last_seen in batch:
                when_clauses.append(f"WHEN {monitor_id} THEN '{last_seen}'")
                monitor_ids.append(str(monitor_id))
            
            # Execute batch update
            sql = text(f"""
                UPDATE monitors 
                SET last_seen_incarcerated = CASE id
                    {' '.join(when_clauses)}
                    ELSE last_seen_incarcerated
                END
                WHERE id IN ({','.join(monitor_ids)})
            """)
            
            try:
                session.execute(sql)
                logger.debug(f"Updated batch of {len(batch)} monitors")
            except Exception as e:
                logger.error(f"Error updating monitor batch: {e}")
        
        session.commit()
    
    @staticmethod
    def batch_update_release_dates(session: Session, release_updates: list[tuple], batch_size: int = 10):
        """
        Batch update release dates to reduce database writes and prevent lock timeouts.
        Uses very small batches and immediate commits to prevent deadlocks.
        
        Args:
            session: SQLAlchemy session
            release_updates: List of (inmate_id, release_date) tuples
            batch_size: Number of updates per batch (small to prevent locks)
        """
        if not release_updates:
            return
        
        logger.info(f"Batch updating release dates for {len(release_updates)} inmates in batches of {batch_size}")
        
        # Use very small batches to prevent lock contention
        successful_updates = 0
        
        for i in range(0, len(release_updates), batch_size):
            batch = release_updates[i:i + batch_size]
            batch_num = i//batch_size + 1
            total_batches = (len(release_updates) + batch_size - 1) // batch_size
            
            logger.debug(f"Processing release date batch {batch_num}/{total_batches} ({len(batch)} inmates)")
            
            # Validate connection before each batch
            if not DatabaseOptimizer.validate_connection(session):
                logger.warning(f"Connection lost before release date batch {batch_num}, reconnecting")
                session = DatabaseOptimizer.get_fresh_session(session)
            
            # Try individual updates to avoid deadlocks completely
            batch_successful = 0
            for inmate_id, release_date in batch:
                retry_count = 0
                max_retries = 3
                update_success = False
                
                while not update_success and retry_count < max_retries:
                    try:
                        # Set a short timeout for this individual operation
                        session.execute(text("SET SESSION innodb_lock_wait_timeout = 30"))
                        
                        # Use simple individual update with immediate commit
                        sql = text("UPDATE inmates SET release_date = :release_date WHERE idinmates = :inmate_id")
                        result = session.execute(sql, {"release_date": release_date, "inmate_id": inmate_id})
                        
                        if result.rowcount > 0:
                            session.commit()  # Commit immediately
                            batch_successful += 1
                            update_success = True
                            logger.trace(f"Updated release date for inmate {inmate_id} to {release_date}")
                        else:
                            logger.warning(f"No rows updated for inmate {inmate_id}")
                            update_success = True  # No need to retry if row doesn't exist
                        
                    except Exception as e:
                        retry_count += 1
                        error_msg = str(e)
                        logger.warning(f"Error updating release date for inmate {inmate_id} (attempt {retry_count}/{max_retries}): {error_msg}")
                        
                        # Roll back this individual transaction
                        try:
                            session.rollback()
                        except:
                            pass
                        
                        if "Lock wait timeout" in error_msg or "Deadlock" in error_msg:
                            # Wait longer for lock issues
                            wait_time = min(5 + (retry_count * 2), 15)
                            logger.debug(f"Lock contention detected, waiting {wait_time}s before retry")
                            time.sleep(wait_time)
                        elif "Lost connection" in error_msg or "Can't reconnect" in error_msg:
                            # Get fresh session for connection issues
                            session = DatabaseOptimizer.get_fresh_session(session)
                        elif retry_count >= max_retries:
                            logger.error(f"Failed to update release date for inmate {inmate_id} after {max_retries} attempts")
                        else:
                            # Brief pause for other errors
                            time.sleep(1)
            
            successful_updates += batch_successful
            
            # Log progress more frequently for large updates
            if len(release_updates) > 50:
                # Log every 5 batches for large updates
                if batch_num % 5 == 0 or batch_num == total_batches:
                    logger.info(f"Release date update progress: {batch_num}/{total_batches} batches completed, {successful_updates} successful updates")
            else:
                # Log every 10 batches for smaller updates
                if batch_num % 10 == 0 or batch_num == total_batches:
                    logger.info(f"Release date update progress: {batch_num}/{total_batches} batches, {successful_updates} successful updates")
        
        logger.info(f"Completed release date updates: {successful_updates}/{len(release_updates)} successful")
        return successful_updates


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
