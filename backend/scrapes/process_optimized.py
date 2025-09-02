"""Optimized process scraped data"""

from datetime import datetime, date
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from loguru import logger
from models.Jail import Jail
from models.Inmate import Inmate
from models.Monitor import Monitor
from helpers.insert_ignore import upsert_inmate


def bulk_upsert_inmates(session: Session, inmates: List[Inmate], batch_size: int = 50):
    """
    Perform bulk upsert of inmates with pre-filtering for large database optimization.
    
    Args:
        session (Session): SQLAlchemy session for database operations.
        inmates (List[Inmate]): List of Inmate objects to upsert.
        batch_size (int): Number of inmates to process in each batch.
    """
    engine = session.get_bind()
    
    if engine.dialect.name == "mysql":
        # Check database size for optimization decisions
        try:
            result = session.execute(text("SELECT COUNT(*) as count FROM inmates")).fetchone()
            total_inmates_in_db = result.count if result else 0
            logger.info(f"Database contains {total_inmates_in_db:,} total inmates")
            
            # For large databases, pre-filter existing records to reduce ON DUPLICATE KEY UPDATE load
            if total_inmates_in_db > 100000:  # 100K+ records
                logger.info("Large database detected - using pre-filtering optimization")
                bulk_upsert_with_prefilter(session, inmates, batch_size)
                return
            
            # Adjust batch size based on database size for smaller databases
            if total_inmates_in_db > 50000:  # 50K+ records
                batch_size = 25
                logger.info(f"Medium database detected, reducing batch size to {batch_size}")
                
        except Exception as db_check_error:
            logger.warning(f"Could not check database size: {db_check_error}")
        
        # Use standard bulk upsert for smaller databases
        standard_bulk_upsert(session, inmates, batch_size)
        
    else:
        # Fallback to individual upserts for non-MySQL databases
        logger.info(f"Using individual upserts for {len(inmates)} inmates (non-MySQL database)")
        for inmate in inmates:
            try:
                upsert_inmate(session, inmate.to_dict())
            except Exception as error:
                logger.error(f"Failed to upsert inmate {inmate.name}: {error}")


def bulk_upsert_with_prefilter(session: Session, inmates: List[Inmate], batch_size: int = 50):
    """
    Optimized bulk upsert that pre-filters existing records to minimize ON DUPLICATE KEY UPDATE operations.
    """
    jail_id = inmates[0].jail_id if inmates else None
    if not jail_id:
        logger.error("No jail_id found for inmates")
        return
        
    logger.info(f"Pre-filtering existing records for jail {jail_id}")
    
    # Get existing inmates for this jail with the key fields we use for uniqueness
    # This is much faster than ON DUPLICATE KEY UPDATE with large datasets
    existing_query = text("""
        SELECT CONCAT(name, '|', COALESCE(race, ''), '|', COALESCE(dob, ''), '|', 
                     COALESCE(sex, ''), '|', COALESCE(arrest_date, ''), '|', jail_id) as unique_key,
               last_seen
        FROM inmates 
        WHERE jail_id = :jail_id
    """)
    
    prefilter_start = datetime.now()
    existing_result = session.execute(existing_query, {"jail_id": jail_id}).fetchall()
    prefilter_end = datetime.now()
    prefilter_duration = (prefilter_end - prefilter_start).total_seconds()
    
    logger.info(f"Pre-filter query completed in {prefilter_duration:.2f}s, found {len(existing_result)} existing records")
    
    # Create lookup set for existing records
    existing_inmates = {}
    for row in existing_result:
        unique_key = row[0]
        last_seen = row[1]
        existing_inmates[unique_key] = last_seen
    
    # Separate inmates into new vs existing
    new_inmates = []
    update_inmates = []
    
    for inmate in inmates:
        # Create the same unique key format
        unique_key = f"{inmate.name}|{inmate.race or ''}|{inmate.dob or ''}|{inmate.sex or ''}|{inmate.arrest_date or ''}|{inmate.jail_id}"
        
        if unique_key in existing_inmates:
            # Check if we need to update last_seen (only if more than 1 hour old)
            existing_last_seen = existing_inmates[unique_key]
            if existing_last_seen is None or (datetime.now() - existing_last_seen).total_seconds() > 3600:
                update_inmates.append(inmate)
        else:
            new_inmates.append(inmate)
    
    logger.info(f"Pre-filter results: {len(new_inmates)} new inmates, {len(update_inmates)} to update")
    
    # Process new inmates with simple INSERT
    if new_inmates:
        logger.info(f"Inserting {len(new_inmates)} new inmates")
        insert_new_inmates(session, new_inmates, batch_size)
    
    # Process updates with targeted UPDATE
    if update_inmates:
        logger.info(f"Updating last_seen for {len(update_inmates)} existing inmates")
        update_existing_inmates(session, update_inmates, batch_size)


def insert_new_inmates(session: Session, inmates: List[Inmate], batch_size: int):
    """Simple INSERT for new inmates (no duplicate checking needed)."""
    for i in range(0, len(inmates), batch_size):
        batch = inmates[i:i + batch_size]
        batch_num = i//batch_size + 1
        total_batches = (len(inmates) + batch_size - 1) // batch_size
        
        logger.info(f"Inserting batch {batch_num}/{total_batches}: {len(batch)} new inmates")
        
        batch_data = []
        for inmate in batch:
            data = inmate.to_dict()
            if 'last_seen' not in data or data['last_seen'] is None:
                data['last_seen'] = datetime.now()
            batch_data.append(data)
        
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
        """)
        
        try:
            start_time = datetime.now()
            session.execute(sql, batch_data)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Insert batch {batch_num} completed in {duration:.2f}s")
        except Exception as error:
            logger.error(f"Failed to insert batch {batch_num}: {error}")


def update_existing_inmates(session: Session, inmates: List[Inmate], batch_size: int):
    """Targeted UPDATE for existing inmates that need last_seen updates."""
    for i in range(0, len(inmates), batch_size):
        batch = inmates[i:i + batch_size]
        batch_num = i//batch_size + 1
        total_batches = (len(inmates) + batch_size - 1) // batch_size
        
        logger.info(f"Updating batch {batch_num}/{total_batches}: {len(batch)} existing inmates")
        
        # Build UPDATE with multiple WHERE conditions
        update_cases = []
        params = {"current_time": datetime.now()}
        
        for j, inmate in enumerate(batch):
            param_prefix = f"inmate_{j}_"
            update_cases.append(f"""
                (name = :{param_prefix}name AND race = :{param_prefix}race AND 
                 dob = :{param_prefix}dob AND sex = :{param_prefix}sex AND 
                 arrest_date = :{param_prefix}arrest_date AND jail_id = :{param_prefix}jail_id)
            """)
            
            params.update({
                f"{param_prefix}name": inmate.name,
                f"{param_prefix}race": inmate.race,
                f"{param_prefix}dob": inmate.dob,
                f"{param_prefix}sex": inmate.sex,
                f"{param_prefix}arrest_date": inmate.arrest_date,
                f"{param_prefix}jail_id": inmate.jail_id,
            })
        
        sql = text(f"""
            UPDATE inmates 
            SET last_seen = :current_time,
                cell_block = CASE 
                    {' '.join([f"WHEN {case} THEN :{f'inmate_{j}_'}cell_block" for j, case in enumerate(update_cases)])}
                    ELSE cell_block END,
                held_for_agency = CASE 
                    {' '.join([f"WHEN {case} THEN :{f'inmate_{j}_'}held_for_agency" for j, case in enumerate(update_cases)])}
                    ELSE held_for_agency END
            WHERE ({' OR '.join(update_cases)})
              AND (last_seen IS NULL OR last_seen < DATE_SUB(NOW(), INTERVAL 1 HOUR))
        """)
        
        # Add the dynamic field values
        for j, inmate in enumerate(batch):
            param_prefix = f"inmate_{j}_"
            params.update({
                f"{param_prefix}cell_block": inmate.cell_block,
                f"{param_prefix}held_for_agency": inmate.held_for_agency,
            })
        
        try:
            start_time = datetime.now()
            result = session.execute(sql, params)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            updated_count = result.rowcount
            logger.info(f"Update batch {batch_num} completed in {duration:.2f}s, updated {updated_count} records")
        except Exception as error:
            logger.error(f"Failed to update batch {batch_num}: {error}")


def standard_bulk_upsert(session: Session, inmates: List[Inmate], batch_size: int):
    """Original bulk upsert logic for smaller databases."""
    logger.info(f"Using standard MySQL bulk upsert for {len(inmates)} inmates in batches of {batch_size}")
    
    # Process in batches to avoid memory issues and long-running transactions
    for i in range(0, len(inmates), batch_size):
        batch_start_time = datetime.now()
        batch = inmates[i:i + batch_size]
        batch_num = i//batch_size + 1
        total_batches = (len(inmates) + batch_size - 1) // batch_size
        
        logger.info(f"Processing batch {batch_num}/{total_batches}: inmates {i+1} to {min(i+batch_size, len(inmates))}")
        
        # Prepare batch data
        batch_data = []
        for inmate in batch:
            data = inmate.to_dict()
            if 'last_seen' not in data or data['last_seen'] is None:
                data['last_seen'] = datetime.now()
            batch_data.append(data)
        
        logger.debug(f"Prepared {len(batch_data)} inmate records for batch {batch_num}")
        
        # Create bulk upsert SQL
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
            # Execute the batch with timing
            logger.debug(f"Executing SQL for batch {batch_num}...")
            query_start_time = datetime.now()
            session.execute(sql, batch_data)
            query_end_time = datetime.now()
            query_duration = (query_end_time - query_start_time).total_seconds()
            
            batch_end_time = datetime.now()
            batch_duration = (batch_end_time - batch_start_time).total_seconds()
            
            logger.info(f"Batch {batch_num}/{total_batches} completed in {batch_duration:.2f}s (SQL: {query_duration:.2f}s)")
            
            # If query took too long, reduce batch size for remaining batches
            if query_duration > 30 and batch_size > 10:
                batch_size = max(10, batch_size // 2)
                logger.warning(f"Slow query detected ({query_duration:.2f}s), reducing batch size to {batch_size}")
                
        except Exception as error:
            batch_end_time = datetime.now()
            batch_duration = (batch_end_time - batch_start_time).total_seconds()
            logger.error(f"Failed to process batch {batch_num} after {batch_duration:.2f}s: {error}")
            
            # Fallback to individual upserts for this batch
            logger.info(f"Falling back to individual upserts for batch {batch_num}")
            individual_start_time = datetime.now()
            
            for j, inmate in enumerate(batch):
                try:
                    upsert_inmate(session, inmate.to_dict())
                    if (j + 1) % 10 == 0:
                        logger.debug(f"Individual upsert progress: {j+1}/{len(batch)} inmates")
                except Exception as individual_error:
                    logger.error(f"Failed to upsert inmate {inmate.name}: {individual_error}")
            
            individual_end_time = datetime.now()
            individual_duration = (individual_end_time - individual_start_time).total_seconds()
            logger.info(f"Individual upserts for batch {batch_num} completed in {individual_duration:.2f}s")
                    
    logger.info(f"Completed bulk upsert of {len(inmates)} inmates")


def process_scrape_data_optimized(session: Session, inmates: List[Inmate], jail: Jail):
    """
    Optimized version of process scraped inmate data and update the database.

    Optimizations:
    - Pre-load all monitors once
    - Create name lookup dictionaries for faster matching
    - Batch database operations
    - Reduce session commits

    Args:
        session (Session): SQLAlchemy session for database operations.
        inmates (List[Inmate]): List of Inmate objects containing scraped data.
        jail (Jail): Jail object containing jail details.

    Returns:
        None
    """
    logger.info(f"Processing {jail.jail_name} (optimized)")

    # Pre-load all monitors once
    monitors = session.query(Monitor).all()

    # Create lookup dictionaries for faster matching
    monitor_by_exact_name: Dict[str, Monitor] = {}
    monitor_partial_matches: List[Monitor] = []

    for monitor in monitors:
        monitor_name = str(monitor.name)
        monitor_by_exact_name[monitor_name] = monitor
        monitor_partial_matches.append(monitor)

    # Process each inmate
    monitors_to_update = []
    new_monitors = []
    inmates_to_insert = []

    for inmate in inmates:
        inmate_processed = False

        # Check for exact name match first (fastest)
        inmate_name = str(inmate.name)
        if inmate_name in monitor_by_exact_name:
            monitor = monitor_by_exact_name[inmate_name]

            # Always update last_seen_incarcerated when monitor is found
            monitor.last_seen_incarcerated = datetime.now()  # type: ignore

            # Check for new arrest date
            if monitor.arrest_date != inmate.arrest_date:
                logger.trace(f"New arrest date for {monitor.name}")
                monitor.arrest_date = inmate.arrest_date
                monitor.release_date = None # type: ignore
                monitor.send_message(inmate)
                inmate_processed = True
            elif (
                inmate.release_date
                and monitor.release_date != inmate.release_date
                and inmate.release_date != ""
            ):
                logger.info(f"New release date for {monitor.name}")
                monitor.release_date = inmate.release_date
                monitor.send_message(inmate, released=True)

            # Always add to update list since we updated last_seen_incarcerated
            monitors_to_update.append(monitor)

        # If no exact match, check for partial matches
        if not inmate_processed:
            for monitor in monitor_partial_matches:
                if monitor.name in inmate.name and monitor.name != inmate.name:
                    logger.info(f"Matched {monitor.name} to {inmate.name}")

                    # Check if there's already an exact match monitor
                    if inmate_name in monitor_by_exact_name:
                        logger.info(
                            f"Found full name match for {inmate.name}, Skipping partial match"
                        )
                        continue

                    if monitor.arrest_date != inmate.arrest_date:
                        logger.trace(
                            f"New arrest date for partial match {monitor.name}"
                        )
                        logger.success(f"Creating new monitor for {inmate.name}")

                        new_monitor = Monitor(  # pylint: disable=unexpected-keyword-arg
                            name=inmate.name,
                            arrest_date=inmate.arrest_date,
                            release_date=None,
                            jail=jail.jail_name,
                            mugshot=inmate.mugshot,
                            enable_notifications=monitor.enable_notifications,
                            notify_method=monitor.notify_method,
                            notify_address=monitor.notify_address,
                            last_seen_incarcerated=datetime.now(),
                        )
                        new_monitors.append(new_monitor)
                        monitor_by_exact_name[inmate_name] = (
                            new_monitor  # Add to lookup for future inmates
                        )
                        monitor.send_message(inmate)
                        break

        # Always try to insert the inmate record with updated last_seen
        inmate.last_seen = datetime.now()
        inmates_to_insert.append(inmate)

    # Batch database operations - handle upserts for inmates
    try:
        # Add new monitors
        if new_monitors:
            logger.info(f"Adding {len(new_monitors)} new monitors")
            for monitor in new_monitors:
                session.add(monitor)

        # Process inmates with true bulk upsert for performance
        if inmates_to_insert:
            logger.info(f"Processing {len(inmates_to_insert)} inmates with bulk upsert")
            bulk_upsert_inmates(session, inmates_to_insert)

        # Commit all changes at once
        session.commit()
        logger.info("Successfully committed all changes")

    except Exception as error:
        logger.error(f"Failed to commit changes: {error}")
        session.rollback()
        raise

    # Check for released inmates (those no longer in jail)
    # TEMPORARILY DISABLED - Commenting out to test before fixing
    # try:
    #     check_for_released_inmates(session, inmates, jail)
    #     # Also check for released inmates in the main inmates table
    #     update_release_dates_for_missing_inmates(session, inmates, jail)
    #     session.commit()
    #     logger.debug("Checked for released inmates and updated release dates")
    # except Exception as error:
    #     logger.error(f"Failed to check for released inmates: {error}")
    #     session.rollback()

    # Update jail's last scrape date
    try:
        jail.update_last_scrape_date()
        session.commit()
        logger.debug("Updated jail last scrape date")
    except Exception as error:
        logger.error(f"Failed to update jail last scrape date: {error}")
        session.rollback()


def check_for_released_inmates(
    session: Session, current_inmates: List[Inmate], jail: Jail
):
    """
    Check for monitors that were previously incarcerated but are no longer
    in the current batch of scraped inmates, indicating they may have been released.

    Args:
        session (Session): SQLAlchemy session for database operations.
        current_inmates (List[Inmate]): List of currently scraped inmates.
        jail (Jail): Jail object containing jail details.
    """
    logger.debug(f"Checking for released inmates in {jail.jail_name}")

    # Get all monitors for this jail that have been seen incarcerated
    # and don't already have a release date
    monitors_to_check = (
        session.query(Monitor)
        .filter(
            Monitor.jail == jail.jail_name,
            Monitor.last_seen_incarcerated.isnot(None),
            Monitor.release_date.is_(None),
        )
        .all()
    )

    if not monitors_to_check:
        logger.debug(f"No monitors to check for releases in {jail.jail_name}")
        return

    logger.debug(f"Found {len(monitors_to_check)} monitors to check for releases")

    # Create a set of current inmate names for fast lookup
    current_inmate_names = {
        str(inmate.name).strip().lower() for inmate in current_inmates
    }

    released_monitors = []

    for monitor in monitors_to_check:
        monitor_name = str(monitor.name).strip().lower()

        # Check if monitor is still in current inmates list
        if monitor_name not in current_inmate_names:
            # Monitor not found in current inmates - likely released
            logger.info(
                f"Monitor {monitor.name} appears to have been released from {jail.jail_name}"
            )

            # Prefer to use the last date the inmate was seen as the release date, if available
            last_seen_date = getattr(monitor, "last_seen_date", None)
            if last_seen_date:
                release_date_str = last_seen_date.strftime("%Y-%m-%d")
                logger.info(f"Setting release date for {monitor.name} to last seen date: '{release_date_str}'")
            else:
                release_date_str = datetime.now().strftime("%Y-%m-%d")
                logger.warning(
                    f"Release date for {monitor.name} is uncertain; using current date '{release_date_str}' as fallback"
                )
            monitor.release_date = release_date_str  # type: ignore
            logger.debug(f"Monitor.release_date is now: '{monitor.release_date}'")

            # Create a dummy inmate object for the release notification
            # We'll use the monitor's stored information
            dummy_inmate = Inmate(  # pylint: disable=unexpected-keyword-arg
                name=monitor.name,
                race="Unknown",
                sex="Unknown",
                cell_block=None,
                arrest_date=monitor.arrest_date,
                held_for_agency=monitor.arresting_agency or "Unknown",
                mugshot=monitor.mugshot,
                dob="Unknown",
                hold_reasons=monitor.arrest_reason or "Unknown",
                is_juvenile=False,
                release_date=release_date_str,
                in_custody_date=monitor.arrest_date or datetime.now().date(),
                jail_id=jail.jail_id,
                hide_record=False,
            )

            # Send release notification
            try:
                monitor.send_message(dummy_inmate, released=True)
                logger.success(f"Sent release notification for {monitor.name}")
            except Exception as error:
                logger.error(
                    f"Failed to send release notification for {monitor.name}: {error}"
                )

            released_monitors.append(monitor)

    if released_monitors:
        logger.info(
            f"Marked {len(released_monitors)} monitors as released from {jail.jail_name}"
        )
    else:
        logger.debug(f"No releases detected in {jail.jail_name}")


def update_release_dates_for_missing_inmates(
    session: Session, current_inmates: List[Inmate], jail: Jail
):
    """
    Update release_date for inmates who are no longer present in the current scrape
    and have a blank release_date, indicating they have been released.

    Args:
        session (Session): SQLAlchemy session for database operations.
        current_inmates (List[Inmate]): List of currently scraped inmates.
        jail (Jail): Jail object containing jail details.
    """
    logger.debug(f"Checking for inmates to update release dates in {jail.jail_name}")

    # Get all inmates for this jail that don't have a release date and last_seen is not today
    today = date.today()
    today_start_dt = datetime.combine(today, datetime.min.time())  # Start of today as datetime
    
    inmates_to_check = (
        session.query(Inmate)
        .filter(
            Inmate.jail_id == jail.jail_id,
            Inmate.release_date.in_(["", None]),  # Blank or null release date
            Inmate.last_seen < today_start_dt  # last_seen is before today
        )
        .all()
    )

    if not inmates_to_check:
        logger.debug(f"No inmates need release date updates in {jail.jail_name}")
        return

    logger.info(f"Found {len(inmates_to_check)} inmates to check for release date updates in {jail.jail_name}")

    # Create a set of current inmate identifiers (name + arrest_date) for fast lookup
    current_inmate_identifiers = {
        (str(inmate.name).strip().lower(), inmate.arrest_date) for inmate in current_inmates
    }
    
    logger.debug(f"Current scrape has {len(current_inmate_identifiers)} unique inmate records")
    logger.debug(f"Checking {len(inmates_to_check)} inmates with old last_seen dates")

    updated_count = 0

    for inmate in inmates_to_check:
        inmate_name = str(inmate.name).strip().lower()
        inmate_identifier = (inmate_name, inmate.arrest_date)

        # Check if this specific incarceration (name + arrest_date) is still in current inmates list
        if inmate_identifier not in current_inmate_identifiers:
            # This specific incarceration not found in current scrape - likely released
            # Use their last_seen date as the release date
            if inmate.last_seen:
                # Extract just the date part from the datetime object
                release_date_str = inmate.last_seen.date().isoformat()
            else:
                # Fallback to today's date if no last_seen
                release_date_str = today.isoformat()
            
            logger.info(
                f"Setting release date for {inmate.name} (arrested: {inmate.arrest_date}) to {release_date_str} (last seen: {inmate.last_seen})"
            )
            
            inmate.release_date = release_date_str
            updated_count += 1
        else:
            logger.debug(f"Inmate {inmate.name} (arrested: {inmate.arrest_date}) still in current roster, skipping release date update")

    if updated_count > 0:
        logger.info(f"Updated release dates for {updated_count} inmates in {jail.jail_name}")
    else:
        logger.debug(f"No release date updates needed in {jail.jail_name}")


# Backward compatibility
def process_scrape_data(session: Session, inmates: List[Inmate], jail: Jail):
    """
    Backward compatible wrapper that uses the optimized processor.
    """
    return process_scrape_data_optimized(session, inmates, jail)
