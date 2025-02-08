"""Incarceration Bot"""

import time
import os
import sys
import schedule
from loguru import logger
from sqlalchemy.orm import Session
from models.Jail import Jail
from scrapes.zuercher import scrape_zuercherportal
from scrapes.washington_so_ar import scrape_washington_so_ar
import database_connect as db
from update_jails_db import update_jails_db


DEFAULT_SCHEDULE: str = "01:00,05:00,09:00,13:00,17:00,21:00"
run_schedule: list = os.getenv("RUN_SCHEDULE", DEFAULT_SCHEDULE).split(",")
enable_jails_containing: list = os.getenv("ENABLE_JAILS_CONTAINING", "benton").split(",")
is_on_demand: bool = True if os.getenv("ON_DEMAND", "False") == "True" else False
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

def enable_jails(session: Session):
    """Enable Jails"""
    logger.info("Enabling/Disabling Jails")
    jails = session.query(Jail).all()
    for jail in jails:
        logger.trace(f"Checking {jail.jail_id}")
        for enable_jail in enable_jails_containing:
            logger.trace(f"Checking {enable_jail}")
            logger.debug(f"Checking {jail.jail_id} for {enable_jail}")
            if enable_jail in jail.jail_id:
                logger.debug(f"Enabling {jail.jail_name}")
                jail.active = True  # type: ignore
            else:
                logger.debug(f"Disabling {jail.jail_name}")
                jail.active = False  # type: ignore
    session.commit()
    return False


def run():
    """Run the bot"""
    logger.info("Starting Bot")
    session = db.Session()
    update_jails_db(session)
    if enable_jails_containing:
        enable_jails(session)
    jails = session.query(Jail).filter(Jail.active == True).all()  # type: ignore
    for jail in jails:
        logger.debug(f"Preparing {jail.jail_name}")
        if jail.scrape_system == "zuercherportal":
            scrape_zuercherportal(session, jail)
        elif jail.scrape_system == "washington_so_ar":
            scrape_washington_so_ar(session, jail)
    session.close()
    logger.success("Bot Finished")


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level=LOG_LEVEL)
    db.Base.metadata.create_all(db.db)
    if is_on_demand:
        logger.info("Running in On Demand Mode.")
        run()
    else:
        logger.info("Running in Normal Production Mode.")
        for time_to_run in run_schedule:
            schedule.every().day.at(time_to_run).do(run)
        while True:
            schedule.run_pending()
            time.sleep(60)
