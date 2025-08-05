# Incarceration Bot
![Docker Image Version](https://img.shields.io/docker/v/justinkumpe/incarceration_bot?sort=semver&logo=docker)
 
This bot is a docker container for scraping jail websites and saving inmate data to your database.

## Project Structure

- `backend/` - Python backend application (main scraping bot + FastAPI web API)
- `frontend/` - React-based web interface for managing inmates and monitors
- `.github/` - GitHub workflows and configurations
- `docker-compose.yml.example` - Example Docker Compose configuration for backend only
- `docker-compose.full.yml` - Full stack Docker Compose with frontend, backend API, scraper, and database

## Current Jails

Feel free to request additional jails (or submit a pull request to add yourself). I am trying to get more jails added as I have time. If the jail uses zuercher portal then it just needs to be added to the jails.json file (or raise issue and I can do it pretty quickly). Other jails need to figure out how to scrape the website first.

| State    | Jail              | Jail ID          | Added In Version | Mugshot                     |
|----------|-------------------|------------------|------------------|-----------------------------|
| Arkansas | Benton County     | benton-so-ar     | 1.0.0            | :white_check_mark:          |
| Arkansas | Pulaski County    | pulaski-so-ar    | 1.0.0            | :white_check_mark:          |
| Arkansas | Washington County | washington-so-ar | 2.0.0            | :white_check_mark: (2.1.3+) |
| Arkansas | Crawford County   | crawford-so-ar   | 2.1.0            | :white_check_mark: (2.1.1+) |
| California | Sutter County   | sutter-so-ca    | 3.0.0            | :white_check_mark: |
| Colorado | Gilpin County   | gilpin-so-co    | 3.0.0            | :white_check_mark: |
| Georgia  | Catoosa County  | catoosa-so-ga   | 3.0.0            | :white_check_mark: |
| Georgia  | Douglas County  | douglas-so-ga   | 3.0.0            | :white_check_mark: |
| Georgia  | Floyd County    | floyd-so-ga     | 3.0.0            | :white_check_mark: |
| Georgia  | Houston County  | houston-so-ga   | 3.0.0            | :white_check_mark: |
| Georgia  | Lumpkin County  | lumpkin-so-ga   | 3.0.0            | :white_check_mark: |
| Georgia  | Toombs County   | toombs-so-ga    | 3.0.0            | :white_check_mark: |
| Idaho    | Clearwater County | clearwater-so-id | 3.0.0            | :white_check_mark: |
| Idaho    | Washington County | washington-so-id | 3.0.0            | :white_check_mark: |
| Illinois | Iroquois County | iroquois-so-il  | 3.0.0            | :white_check_mark: |
| Illinois | Ogle County     | ogle-so-il      | 3.0.0            | :white_check_mark: |
| Illinois | Whiteside County | whiteside-so-il | 3.0.0            | :white_check_mark: |
| Indiana  | Marshall County | marshall-so-in  | 3.0.0            | :white_check_mark: |
| Indiana  | Wayne County    | wayne-so-in     | 3.0.0            | :white_check_mark: |
| Iowa     | Clinton County  | clinton-so-ia   | 3.0.0            | :white_check_mark: |
| Iowa     | Marshall County | marshall-so-ia  | 3.0.0            | :white_check_mark: |
| Iowa     | Pottawattamie County | pottawattamie-so-ia | 3.0.0            | :white_check_mark: |
| Iowa     | Poweshiek County | poweshiek-so-ia | 3.0.0            | :white_check_mark: |
| Iowa     | Wapello County  | wapello-so-ia   | 3.0.0            | :white_check_mark: |
| Iowa     | Webster County  | webster-so-ia   | 3.0.0            | :white_check_mark: |
| Iowa     | Winneshiek County | winneshiek-so-ia | 3.0.0            | :white_check_mark: |
| Kansas   | Atchison County | atchison-so-ks  | 3.0.0            | :white_check_mark: |
| Kansas   | Leavenworth County | leavenworth-so-ks | 3.0.0            | :white_check_mark: |
| Kansas   | Linn County     | linn-so-ks      | 3.0.0            | :white_check_mark: |
| Louisiana | Acadia County   | acadia-so-la    | 3.0.0            | :white_check_mark: |
| Louisiana | Assumption County | assumption-so-la | 3.0.0            | :white_check_mark: |
| Louisiana | Bienville County | bienville-so-la | 3.0.0            | :white_check_mark: |
| Louisiana | Jackson County  | jackson-so-la   | 3.0.0            | :white_check_mark: |
| Louisiana | Lafourche County | lafourche-so-la | 3.0.0            | :white_check_mark: |
| Maine    | Androscoggin County | androscoggin-so-me | 3.0.0            | :white_check_mark: |
| Maine    | Franklin County | franklin-so-me  | 3.0.0            | :white_check_mark: |
| Maine    | Lincoln County  | lincoln-so-me   | 3.0.0            | :white_check_mark: |
| Michigan | Monroe County   | monroe-so-mi    | 3.0.0            | :white_check_mark: |
| Minnesota | Pine County     | pine-so-mn      | 3.0.0            | :white_check_mark: |
| Missouri | Bates County    | bates-so-mo     | 3.0.0            | :white_check_mark: |
| Missouri | Jackson County  | jackson-so-mo   | 3.0.0            | :white_check_mark: |
| Montana  | Broadwater County | broadwater-so-mt | 3.0.0            | :white_check_mark: |
| Montana  | Carbon County   | carbon-so-mt    | 3.0.0            | :white_check_mark: |
| Montana  | Chouteau County | chouteau-so-mt  | 3.0.0            | :white_check_mark: |
| Montana  | Gallatin County | gallatin-so-mt  | 3.0.0            | :white_check_mark: |
| Montana  | Jefferson County | jefferson-so-mt | 3.0.0            | :white_check_mark: |
| Montana  | Madison County  | madison-so-mt   | 3.0.0            | :white_check_mark: |
| Montana  | Meagher County  | meagher-so-mt   | 3.0.0            | :white_check_mark: |
| Montana  | Ravalli County  | ravalli-so-mt   | 3.0.0            | :white_check_mark: |
| Montana  | Roosevelt County | roosevelt-so-mt | 3.0.0            | :white_check_mark: |
| Montana  | Rosebud County  | rosebud-so-mt   | 3.0.0            | :white_check_mark: |
| Montana  | Stillwater County | stillwater-so-mt | 3.0.0            | :white_check_mark: |
| Montana  | Valley County   | valley-so-mt    | 3.0.0            | :white_check_mark: |
| Nebraska | Johnson County  | johnson-so-ne   | 3.0.0            | :white_check_mark: |
| Nebraska | Perkins County  | perkins-so-ne   | 3.0.0            | :white_check_mark: |
| New Hampshire | Rockingham County | rockingham-so-nh | 3.0.0            | :white_check_mark: |
| New Mexico | Hidalgo County  | hidalgo-so-nm   | 3.0.0            | :white_check_mark: |
| North Carolina | Brunswick County | brunswick-so-nc | 3.0.0            | :white_check_mark: |
| North Carolina | Davie County    | davie-so-nc     | 3.0.0            | :white_check_mark: |
| North Carolina | Hoke County     | hoke-so-nc      | 3.0.0            | :white_check_mark: |
| North Carolina | Pender County   | pender-so-nc    | 3.0.0            | :white_check_mark: |
| North Carolina | Rutherford County | rutherford-so-nc | 3.0.0            | :white_check_mark: |
| North Dakota | Williams County | williams-so-nd  | 3.0.0            | :white_check_mark: |
| Ohio     | Ashland County  | ashland-so-oh   | 3.0.0            | :white_check_mark: |
| Ohio     | Athens County   | athens-so-oh    | 3.0.0            | :white_check_mark: |
| Ohio     | Fayette County  | fayette-so-oh   | 3.0.0            | :white_check_mark: |
| Ohio     | Marion County   | marion-so-oh    | 3.0.0            | :white_check_mark: |
| Ohio     | Medina County   | medina-so-oh    | 3.0.0            | :white_check_mark: |
| Ohio     | Paulding County | paulding-so-oh  | 3.0.0            | :white_check_mark: |
| Ohio     | Pickaway County | pickaway-so-oh  | 3.0.0            | :white_check_mark: |
| Ohio     | Pike County     | pike-so-oh      | 3.0.0            | :white_check_mark: |
| Ohio     | Preble County   | preble-so-oh    | 3.0.0            | :white_check_mark: |
| Ohio     | Ross County     | ross-so-oh      | 3.0.0            | :white_check_mark: |
| Ohio     | Scioto County   | scioto-so-oh    | 3.0.0            | :white_check_mark: |
| Ohio     | Shelby County   | shelby-so-oh    | 3.0.0            | :white_check_mark: |
| Oklahoma | Cleveland County | cleveland-so-ok | 3.0.0            | :white_check_mark: |
| Oregon   | Clatsop County  | clatsop-so-or   | 3.0.0            | :white_check_mark: |
| South Carolina | Anderson County | anderson-so-sc  | 3.0.0            | :white_check_mark: |
| South Carolina | Cherokee County | cherokee-so-sc  | 3.0.0            | :white_check_mark: |
| South Carolina | Colleton County | colleton-so-sc  | 3.0.0            | :white_check_mark: |
| South Carolina | Kershaw County  | kershaw-so-sc   | 3.0.0            | :white_check_mark: |
| South Carolina | Oconee County   | oconee-so-sc    | 3.0.0            | :white_check_mark: |
| South Carolina | Pickens County  | pickens-so-sc   | 3.0.0            | :white_check_mark: |
| South Carolina | Union County    | union-so-sc     | 3.0.0            | :white_check_mark: |
| South Carolina | Williamsburg County | williamsburg-so-sc | 3.0.0            | :white_check_mark: |
| South Dakota | Bennett County  | bennett-so-sd   | 3.0.0            | :white_check_mark: |
| South Dakota | Clay County     | clay-so-sd      | 3.0.0            | :white_check_mark: |
| South Dakota | Custer County   | custer-so-sd    | 3.0.0            | :white_check_mark: |
| South Dakota | Davison County  | davison-so-sd   | 3.0.0            | :white_check_mark: |
| South Dakota | Lake County     | lake-so-sd      | 3.0.0            | :white_check_mark: |
| South Dakota | Lawrence County | lawrence-so-sd  | 3.0.0            | :white_check_mark: |
| South Dakota | Lincoln County  | lincoln-so-sd   | 3.0.0            | :white_check_mark: |
| South Dakota | Lyman County    | lyman-so-sd     | 3.0.0            | :white_check_mark: |
| South Dakota | Marshall County | marshall-so-sd  | 3.0.0            | :white_check_mark: |
| South Dakota | Meade County    | meade-so-sd     | 3.0.0            | :white_check_mark: |
| South Dakota | Pennington County | pennington-so-sd | 3.0.0            | :white_check_mark: |
| South Dakota | Roberts County  | roberts-so-sd   | 3.0.0            | :white_check_mark: |
| South Dakota | Sully County    | sully-so-sd     | 3.0.0            | :white_check_mark: |
| South Dakota | Union County    | union-so-sd     | 3.0.0            | :white_check_mark: |
| South Dakota | Yankton County  | yankton-so-sd   | 3.0.0            | :white_check_mark: |
| Tennessee | Sullivan County | sullivan-so-tn  | 3.0.0            | :white_check_mark: |
| Tennessee | Washington County | washington-so-tn | 3.0.0            | :white_check_mark: |
| Texas    | Brooks County   | brooks-so-tx    | 3.0.0            | :white_check_mark: |
| Texas    | Presidio County | presidio-so-tx  | 3.0.0            | :white_check_mark: |
| Texas    | Upshur County   | upshur-so-tx    | 3.0.0            | :white_check_mark: |
| Virginia | Caroline County | caroline-so-va  | 3.0.0            | :white_check_mark: |
| Virginia | Northumberland County | northumberland-so-va | 3.0.0            | :white_check_mark: |
| Wisconsin | Dunn County     | dunn-so-wi      | 3.0.0            | :white_check_mark: |
| Wisconsin | Grant County    | grant-so-wi     | 3.0.0            | :white_check_mark: |
| Wisconsin | Lincoln County  | lincoln-so-wi   | 3.0.0            | :white_check_mark: |
| Wisconsin | Menominee County | menominee-so-wi | 3.0.0            | :white_check_mark: |
| Wisconsin | Monroe County   | monroe-so-wi    | 3.0.0            | :white_check_mark: |
| Wisconsin | Washburn County | washburn-so-wi  | 3.0.0            | :white_check_mark: |
| Wyoming  | Teton County    | teton-so-wy     | 3.0.0            | :white_check_mark: |

## Web Interface

The project now includes a modern React-based web interface that provides:

- **Dashboard**: Overview of system statistics and recent activity
- **Inmate Search**: Search and view detailed inmate information across all monitored jails
- **Monitor Management**: Add, edit, and manage arrest monitors with notification settings
- **User Management**: User authentication and role-based access control
- **Jail Management**: View and manage jail configurations

### Quick Start with Web Interface

1. Copy the environment file and configure your settings:

   ```bash
   cp .env.example .env
   # Edit .env with your database and other configuration
   ```

2. Start the full stack (frontend, API, scraper, and database):

   ```bash
   docker-compose -f docker-compose.full.yml up -d
   ```

3. Access the web interface:
   - Frontend: <http://localhost:3000>
   - API Documentation: <http://localhost:8000/docs>
   - Database Admin: <http://localhost:8080>

4. Default login credentials:
   - Admin: username `admin`, password `admin123`
   - User: username `user`, password `user123`

### Example Docker Compose File

```yaml
services:
  incarceration_bot:
    image: "justinkumpe/incarceration_bot:latest"
    # For local development, uncomment the following and comment out the image line above:
    # build:
    #   context: ./backend
    #   dockerfile: Dockerfile
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
      # - FETCH_MUGSHOTS=<True/False> # Default is False. Enable to fetch mugshots for inmates.
      # - MUGSHOT_TIMEOUT=<seconds> # Default is 5. Timeout in seconds for fetching mugshots.
```
