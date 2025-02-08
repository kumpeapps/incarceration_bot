"""Update jails database with new data from jails.json"""

import json
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from loguru import logger
from models.Jail import Jail
from database_connect import Session as DBSession


def update_jails_db(session: Session, filename: str = "jails.json"):
    """
    Update jails database with new data from jails.json.

    Args:
        session (Session): SQLAlchemy session for database operations.
        filename (str): Filename for the JSON input. Default is "jails.json".

    Returns:
        None
    """
    logger.info("Updating Jail Database")
    with open(filename, "r") as file:
        jails = json.load(file)
    for jail in jails:
        db_jail = session.query(Jail).filter(Jail.jail_id == jail["jail_id"]).first()
        if db_jail:
            if str(db_jail.updated_date) != jail["updated_date"]:
                logger.info(f"Updating {jail['jail_name']}")
                db_jail.jail_name = jail["jail_name"]
                db_jail.state = jail["state"]
                db_jail.scrape_system = jail["scrape_system"]
                db_jail.updated_date = jail["updated_date"]
        else:
            logger.info(f"Adding {jail['jail_name']}")
            new_jail = Jail(  # pylint: disable=unexpected-keyword-arg
                jail_name=jail["jail_name"],
                state=jail["state"],
                jail_id=jail["jail_id"],
                scrape_system=jail["scrape_system"],
                created_date=jail["created_date"],
                updated_date=jail["updated_date"],
                active=False,
            )
            session.add(new_jail)
    try:
        session.commit()
    except IntegrityError:
        logger.error("Integrity Error")
        session.rollback()
    logger.success("Jail Database Updated")


if __name__ == "__main__":
    session = DBSession()
    update_jails_db(session)
    session.close()
