"""Monitor Jails for new arrests"""

import sys
import json
import zuercherportal_api as zuercherportal
import pymysql
from loguru import logger
import requests
from params import Params

arrested_names = []


def get_monitor_list():
    """Get list of users to monitor"""
    logger.trace("get monitor list")
    database = mysql_connect()
    cursor = database.cursor(pymysql.cursors.DictCursor)
    sql = "SELECT * FROM BOT_Data.incarcerationbot__jail_monitor;"
    cursor.execute(sql)
    monitor_list = cursor.fetchall()
    cursor.close()
    database.close()
    return monitor_list


def scrape_zuercherportal(jail: str):
    """Get Inmate Records from a Zuercher Portal"""
    logger.trace("scrape zuercher portal")
    jail_api = zuercherportal.API(jail, log_level="INFO")
    logger.trace("get inmate data")
    inmate_data = jail_api.inmate_search(records_per_page=10000)
    inmate_list = inmate_data["records"]
    monitor_names = []
    monitor_list = get_monitor_list()
    for user in monitor_list:
        logger.trace("build monitor names list")
        monitor_names.append(user["name"])
    logger.debug(f"Monitor names {monitor_names}")
    logger.trace("Loop thru inmates")
    for inmate in inmate_list:
        logger.trace("Next Inmate")
        if inmate["name"] in monitor_names:
            inmate_name = inmate["name"]
            logger.debug(f"{inmate_name} found in jail database")
            arrested_names.append(inmate["name"])
            process_arrested_user(inmate)


def process_arrested_user(inmate: object):
    """Process Identified Inmate"""
    logger.trace("process arrested user")
    monitor_list = get_monitor_list()
    for user in monitor_list:
        logger.trace("for loop")
        if user["name"] == inmate["name"]:
            logger.debug("found arrest")
            if inmate["arrest_date"] != user["arrest_date"]:
                logger.debug("found new arrest")
                new_monitored_arrest(inmate, user)
            elif inmate["release_date"] != user["release_date"]:
                logger.debug("found new release")
                new_monitored_release(inmate, user)


def new_monitored_arrest(inmate: object, user: object):
    """Process as new arrest"""
    send_message(
        f"{inmate['name']} Arrested",
        f"{inmate['name']} has been arrested by {inmate['held_for_agency']} for {inmate['hold_reasons']}",
    )
    update_monitored_user(inmate)


def new_monitored_release(inmate: object, user: object):
    """Process as inmate released"""
    send_message(f"{inmate['name']} Released", f"{inmate['name']} has been released.")
    update_monitored_user(inmate)


def update_monitored_user(inmate: object):
    """Update monitor database"""
    database = mysql_connect()
    cursor = database.cursor(pymysql.cursors.DictCursor)
    sql = """
            UPDATE BOT_Data.incarcerationbot__jail_monitor
            SET arrest_date = %s,
                release_date = %s,
                arrest_reason = %s,
                arresting_agency = %s
            WHERE 1=1
                AND name = %s;
        """
    cursor.execute(
        sql,
        (
            inmate["arrest_date"],
            inmate["release_date"],
            inmate["hold_reasons"],
            inmate["held_for_agency"],
            inmate["name"],
        ),
    )
    database.commit()
    cursor.close()


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


def send_message(title: str, message: str):
    """Send Pushover Message"""

    try:
        _ = requests.post(
            url="https://api.pushover.net/1/messages.json",
            headers={
                "Content-Type": "application/json; charset=utf-8",
            },
            data=json.dumps(
                {
                    "sound": "siren",
                    "message": message,
                    "title": title,
                    "priority": "1",
                    "token": Params.PushOver.api_key,
                    "user": Params.PushOver.group,
                }
            ),
            timeout=10,
        )
    except requests.exceptions.RequestException:
        logger.exception("")


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    get_monitor_list()
    scrape_zuercherportal(zuercherportal.Jails.AR.BENTON_COUNTY)
    scrape_zuercherportal(zuercherportal.Jails.AR.PULASKI_COUNTY)
