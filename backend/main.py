"""Incarceration Bot"""

import time
import os
from datetime import datetime, timedelta
import sys
import schedule
import requests  # type: ignore
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError
import models  # Import models package to register all models with SQLAlchemy
from models.Jail import Jail, Inmate
from scrapes.zuercher import scrape_zuercherportal
from scrapes.crawford_so_ar import scrape_crawford_so_ar
from scrapes.washington_so_ar_optimized import scrape_washington_so_ar_optimized
from scrapes.aiken_so_sc_optimized import scrape_aiken_so_sc_optimized
import database_connect as db
from update_jails_db import update_jails_db


DEFAULT_SCHEDULE: str = "01:00,05:00,09:00,13:00,17:00,21:00"
run_schedule: list = os.getenv("RUN_SCHEDULE", DEFAULT_SCHEDULE).split(",")
enable_jails_containing: list = os.getenv("ENABLE_JAILS_CONTAINING", "-").split(",")
is_on_demand: bool = True if os.getenv("ON_DEMAND", "False") == "True" else False
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
HEARTBEAT_WEBHOOK = os.getenv("HEARTBEAT_WEBHOOK", None)
LOOP_DELAY = int(os.getenv("LOOP_DELAY", "20"))
LOG_FILE = os.getenv("LOG_FILE", None)
DELETE_MUGSHOTS_AFTER_DAYS = int(os.getenv("DELETE_MUGSHOTS_AFTER_DAYS", "30"))


def enable_jails(session: Session):
    """Enable Jails"""
    logger.info("Enabling/Disabling Jails")
    jails = session.query(Jail).all()
    for jail in jails:
        logger.trace(f"Checking {jail.jail_id}")
        # Start with jail disabled
        jail.active = False  # type: ignore

        # Check each criteria - if any match, enable the jail
        for enable_jail in enable_jails_containing:
            logger.trace(f"Checking criterion: {enable_jail}")
            logger.debug(f"Checking if {jail.jail_id} contains {enable_jail}")

            if enable_jail in jail.jail_id:
                logger.debug(f"Enabling {jail.jail_name} (matched {enable_jail})")
                jail.active = True  # type: ignore
                break  # No need to check other criteria once we've enabled

    session.commit()

    # Log summary of what's enabled
    enabled_count = session.query(Jail).filter(Jail.active == True).count()  # type: ignore
    enabled_jails = session.query(Jail).filter(Jail.active == True).all()  # type: ignore
    logger.info(f"Enabled {enabled_count} jails:")
    for jail in enabled_jails:
        logger.info(f"  - {jail.jail_name} ({jail.jail_id})")

    return False


def run():
    """Run the bot"""
    logger.info("Starting Bot")
    session = db.new_session()
    if enable_jails_containing:
        enable_jails(session)
    jails = session.query(Jail).filter(Jail.active == True).all()  # type: ignore
    logger.debug(jails)
    jails_completed = 0
    jails_total = len(jails)
    success_jails = []
    failed_jails = []
    logger.info(f"Running for {jails_total} Jails")
    for jail in jails:

        def run_scrape(scrape_method, session, jail):
            nonlocal jails_completed
            logger.debug(
                f"Run Scrape: Scraping {jail.jail_name} ({jail.scrape_system})"
            )
            try:
                scrape_method(session, jail)
                jails_completed += 1
                success_jails.append(jail.jail_name)
            except Exception:
                logger.exception(f"Failed to scrape {jail.jail_name}")
                failed_jails.append(jail.jail_name)

        logger.debug(f"Preparing {jail.jail_name}")
        if jail.scrape_system == "zuercherportal":
            logger.debug(
                f"If scraping system: Scraping {jail.jail_name} with Zuercher Portal"
            )
            run_scrape(scrape_zuercherportal, session, jail)
        elif jail.scrape_system == "washington_so_ar":
            logger.debug(
                f"If scraping system: Scraping {jail.jail_name} with Washington SO AR"
            )
            run_scrape(scrape_washington_so_ar_optimized, session, jail)
        elif jail.scrape_system == "crawford_so_ar":
            logger.debug(
                f"If scraping system: Scraping {jail.jail_name} with Crawford SO AR"
            )
            run_scrape(scrape_crawford_so_ar, session, jail)
        elif jail.scrape_system == "aiken_so_sc":
            logger.debug(
                f"If scraping system: Scraping {jail.jail_name} with Aiken County SC (Optimized)"
            )
            run_scrape(scrape_aiken_so_sc_optimized, session, jail)
        logger.info(f"Completed {jails_completed}/{jails_total} Jails")
    # delete_old_mugshots(session)
    session.close()
    if HEARTBEAT_WEBHOOK:
        logger.info("Sending Webhook Notification")
        if jails_completed == jails_total:
            notify_message = f"{jails_completed} Jails Successfully Completed"
        elif jails_completed == 0:
            notify_message = f"{jails_total} Jails Failed"
        else:
            notify_message = (
                f"Partial Success ({jails_total - jails_completed} Degraded)"
            )

        try:
            response = requests.post(
                HEARTBEAT_WEBHOOK,
                json={
                    "message": notify_message,
                    "jails_completed": success_jails,
                    "failed_jails": failed_jails,
                },
                headers={"Content-Type": "application/json"},
                timeout=30,  # Increased timeout to 30 seconds
            )
            logger.success(f"Webhook notification sent successfully (status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to send webhook notification (non-critical): {e}")
            # Don't let webhook failures crash the bot
    logger.success("Bot Finished")


def delete_old_mugshots(session: Session):
    """Delete old mugshots"""
    logger.info("Deleting Old Mugshots")

    cutoff_date = datetime.now() - timedelta(days=DELETE_MUGSHOTS_AFTER_DAYS)
    query = session.query(Inmate).filter(
        Inmate.mugshot.isnot(None),
        Inmate.mugshot != "",
        Inmate.in_custody_date < cutoff_date,
    )
    num_deleted = query.update({Inmate.mugshot: None}, synchronize_session=False)
    session.commit()
    logger.info(f"Deleted mugshots for {num_deleted} inmates.")


def wait_for_database_ready(max_retries: int = 30, retry_delay: int = 5) -> bool:
    """
    Wait for the database to be ready with all required tables.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay in seconds between retries
        
    Returns:
        bool: True if database is ready, False if timeout
    """
    required_tables = ['jails', 'inmates', 'users', 'groups', 'monitors']
    
    for attempt in range(max_retries):
        try:
            session = db.new_session()
            
            # Check if all required tables exist
            missing_tables = []
            for table in required_tables:
                try:
                    session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                except (OperationalError, ProgrammingError) as e:
                    if 'doesn\'t exist' in str(e) or 'does not exist' in str(e):
                        missing_tables.append(table)
                    else:
                        raise
            
            session.close()
            
            if not missing_tables:
                logger.info("✅ Database is ready - all required tables exist!")
                return True
            else:
                logger.info(f"⏳ Database not ready yet - missing tables: {missing_tables}")
                logger.info(f"🔄 Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...")
                
        except Exception as e:
            logger.warning(f"⚠️  Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
            try:
                session.close()
            except:
                pass
        
        if attempt < max_retries - 1:  # Don't sleep on the last attempt
            time.sleep(retry_delay)
    
    logger.error(f"❌ Database not ready after {max_retries} attempts - giving up")
    return False


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stdout, level=LOG_LEVEL)
    if LOG_FILE:
        logger.add(LOG_FILE, level=LOG_LEVEL)
    
    # Wait for database to be ready before proceeding
    logger.info("🚀 Starting Incarceration Bot - waiting for database to be ready...")
    if not wait_for_database_ready():
        logger.error("❌ Failed to connect to database - exiting")
        sys.exit(1)
    
    session = db.new_session()
    update_jails_db(session)
    session.close()
    if is_on_demand:
        logger.info("Running in On Demand Mode.")
        run()
    else:
        logger.info("Running in Normal Production Mode.")
        for time_to_run in run_schedule:
            schedule.every().day.at(time_to_run).do(run)
        while True:
            logger.debug("Running Scheduled Jobs")
            schedule.run_pending()
            time.sleep(int(LOOP_DELAY))
