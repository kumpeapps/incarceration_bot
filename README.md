# Incarceration Bot
![Docker Image Version](https://img.shields.io/docker/v/justinkumpe/incarceration_bot?sort=semver&logo=docker)
 
This bot is a docker container for scraping jail websites and saving inmate data to your database.

### Current Jails
##### Feel free to request additional jails (or submit a pull request to add yourself). I am trying to get more jails added as I have time. If the jail uses zuercher portal then it just needs to be added to the jails.json file (or raise issue and I can do it pretty quickly). Other jails need to figure out how to scrape the website first
| State    | Jail              | Jail ID          | Added In Version | Mugshot                     |
|----------|-------------------|------------------|------------------|-----------------------------|
| Arkansas | Benton County     | benton-so-ar     | 1.0.0            | :white_check_mark:          |
| Arkansas | Pulaski County    | pulaski-so-ar    | 1.0.0            | :white_check_mark:          |
| Arkansas | Washington County | washington-so-ar | 2.0.0            | :white_check_mark: (2.1.3+) |
| Arkansas | Crawford County   | crawford-so-ar   | 2.1.0            | :white_check_mark: (2.1.1+) |

### Example Docker Compose File
```
services:
  incarceration_bot:
    image: "incarceration_bot:latest"
    environment:
      # - TZ=America/Chicago # Defaults to UTC if not specified
      # - DATABASE_URI=<database_uri> #(only if not using mysql variables)
      # - MYSQL_SERVER=<mysql_server>
      # - MYSQL_USERNAME=<mysql_username>
      # - MYSQL_PASSWORD=<mysql_password>
      # - MYSQL_DATABASE=<mysql_database>
      # - MYSQL_PORT=<mysql_port> # default is 3306 if not specified
      # - PUSHOVER_API_KEY=<pushover_api_key> # Pushover disabled if not specified
      # - PUSHOVER_PRIORITY=<pushover_priority> # default 1 if not specified
      # - PUSHOVER_SOUND=<pushover_sound> # Pushover default used if not specified
      # - RUN_SCHEDULE=<hours to run in 00:00 format comma-separated> # If not specified default is 01:00,05:00,09:00,13:00,17:00,21:00
      # - ENABLE_JAILS_CONTAINING=<comma-separated list of jails to enable> # this enables jails that contain specified strings. Default is all jails enabled. Example: for all jails (in our database) in AR input ar.
      # - ON_DEMAND=<True/False> # Default is False. Set this to True to bypass schedule running all enabled jails immediately then exit.
      # - HEARTBEAT_WEBHOOK=<webhook_url> # Optional. Sends POST to given webhook at end of each run cycle.
```