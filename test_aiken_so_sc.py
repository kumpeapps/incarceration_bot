#!/usr/bin/env python3
"""Test Aiken County SC Scraper"""

import os
import sys
from loguru import logger
import database_connect as db
from models.Jail import Jail
from scrapes.aiken_so_sc import scrape_aiken_so_sc

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logger.remove()
logger.add(sys.stdout, level=LOG_LEVEL)

def main():
    """Test Aiken County SC Scraper"""
    session = db.new_session()
    
    # Check if jail exists in the database
    jail = session.query(Jail).filter(Jail.jail_id == "aiken_so_sc").first()
    
    # If it doesn't exist, create it
    if not jail:
        logger.info("Creating Aiken County SC jail entry")
        jail = Jail(
            jail_name="Aiken County Detention Center",
            state="SC",
            jail_id="aiken_so_sc",
            scrape_system="aiken_so_sc",
            active=True
        )
        session.add(jail)
        session.commit()
    
    # Run the scraper
    logger.info("Starting scrape of Aiken County SC jail")
    scrape_aiken_so_sc(session, jail)
    
    # Close the session
    session.close()
    logger.success("Test completed successfully")

if __name__ == "__main__":
    main()
