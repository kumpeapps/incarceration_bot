import jail_monitor
from datetime import date, timedelta
from loguru import logger

# monitor_list = jail_monitor.get_monitor_list()

def daterange(start_date: date, end_date: date):
    days = int((end_date - start_date).days)
    for n in range(days):
        yield start_date + timedelta(n)

def loop_days():
    start_date = date(2024, 2, 8)
    end_date = date(2024, 9, 14)
    for single_date in daterange(start_date, end_date):
        search_date = single_date.strftime("%Y-%m-%d")
        formated_date = f"{search_date}T00:12:23.656Z"
        jail_monitor.scrape_zuercherportal('benton-so-ar', formated_date)
        jail_monitor.scrape_zuercherportal('pulaski-so-ar', formated_date)
        logger.success(search_date)


if __name__ == "__main__":
    loop_days()