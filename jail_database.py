"""Monitor Jails and add inmates to database"""

import sys
from dataclasses import dataclass
from typing import List as PyList
from datetime import date
import requests
import zuercherportal_api as zuercherportal
from zuercherportal_api import Inmate, ZuercherportalResponse
import pymysql
from loguru import logger
from dataclass_wizard import fromdict
from params import Params
import washington_so_ar

jail_inmate_counts: dict[str, int] = {}


@dataclass
class Jail:
    """Jail"""

    jail_name: str
    state: str
    jail_id: str
    scrape_system: str


@dataclass
class JailData:
    """Jail Data"""

    jails: PyList["Jail"]


def get_jail_database() -> JailData:
    """Get list of users to monitor"""
    logger.trace("get jail database")
    database = mysql_connect()
    cursor = database.cursor(pymysql.cursors.DictCursor)
    sql = """
        SELECT 
            jail_name,
            state,
            jail_id,
            scrape_system
        FROM
            Apps_JailDatabase.jails
        WHERE 1=1
            AND `active`;
    """
    cursor.execute(sql)
    jail_database = cursor.fetchall()
    cursor.close()
    database.close()
    jail_data = {"jails": jail_database}
    jail_data = fromdict(JailData, jail_data)
    return jail_data


def scrape_zuercherportal(jail: Jail, log_level: str = "INFO"):
    """Get Inmate Records from a Zuercher Portal"""
    logger.trace("scrape zuercher portal")
    jail_api = zuercherportal.API(jail.jail_id, log_level=log_level, return_object=True)
    logger.trace("get inmate data")
    inmate_data: ZuercherportalResponse = jail_api.inmate_search(records_per_page=10000)
    inmate_list = inmate_data.records
    database = mysql_connect()
    cursor = database.cursor(pymysql.cursors.DictCursor)
    for inmate in inmate_list:
        insert_incarceration_data(cursor, inmate, jail)
    cursor.execute("call Apps_JailDatabase.log_sync(%s);", jail.jail_id)
    database.commit()
    cursor.close()
    jail_inmate_counts[jail.jail_name] = len(inmate_list)


def scrape_washington_so_ar(jail: Jail):
    """Get Inmate Records from Washington Count AR"""
    inmate_list = washington_so_ar.get_data()
    database = mysql_connect()
    cursor = database.cursor(pymysql.cursors.DictCursor)
    for inmate in inmate_list:
        insert_incarceration_data(cursor, inmate, jail)
    cursor.execute("call Apps_JailDatabase.log_sync(%s);", jail.jail_id)
    database.commit()
    cursor.close()
    jail_inmate_counts[jail.jail_name] = len(inmate_list)


def insert_incarceration_data(
    cursor, inmate: Inmate, jail: Jail, incarceration_date: str = f"{date.today()}"
):
    """Insert to Incarceration Database"""
    sql = """
            INSERT IGNORE INTO `Apps_JailDatabase`.`incarcerations`
                (
                    `in_custody_date`,
                    `name`,
                    `arrest_date`,
                    `arrest_reason`,
                    `arresting_agency`,
                    `jail`,
                    `mugshot`,
                    `sex`,
                    `dob`,
                    `race`
                )
            VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                );
        """
    cursor.execute(
        sql,
        (
            incarceration_date,
            inmate.name,
            inmate.arrest_date,
            inmate.hold_reasons,
            inmate.held_for_agency,
            jail.jail_id,
            inmate.mugshot,
            inmate.sex,
            inmate.dob,
            inmate.race,
        ),
    )


def mysql_connect():
    """Connect to MySQL"""
    database = pymysql.connect(
        db=Params.SQL.database,
        user=Params.SQL.username,
        passwd=Params.SQL.password,
        host=Params.SQL.server,
        port=3306,
    )
    return database


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    jails_data = get_jail_database()
    for jail_data in jails_data.jails:
        if jail_data.scrape_system == "zuercherportal":
            scrape_zuercherportal(jail_data)
        elif jail_data.scrape_system == "washington_so_ar":
            scrape_washington_so_ar(jail_data)
        else:
            logger.error(
                f"Scrape System {jail_data.scrape_system} is not yet configured."
            )
    ONEUPTIME_URL = "https://oneuptime.vm.kumpeapps.com/heartbeat/29bf6ed1-e0ec-11ef-a1c8-dbe03cc3d472"

    data = {
        "status": "success",
        "inmate_counts": jail_inmate_counts,
    }
    try:
        requests.post(ONEUPTIME_URL, data=data, timeout=5)
    except requests.exceptions.RequestException:
        pass
    finally:
        logger.info("Oneuptime Heartbeat Sent")
