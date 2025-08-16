# Incarceration Bot
![Docker Image Version](https://img.shields.io/docker/v/justinkumpe/incarceration_bot?sort=semver&logo=docker)
![Docker API Version](https://img.shields.io/docker/v/justinkumpe/incarceration_bot_api?sort=semver&logo=docker&label=API)
![Docker Frontend Version](https://img.shields.io/docker/v/justinkumpe/incarceration_bot_frontend?sort=semver&logo=docker&label=Frontend)
 
A comprehensive jail monitoring system that scrapes inmate data from county jail websites and provides a modern web interface for monitoring arrests and managing notifications.

## 🌟 Key Features

- **Multi-Jail Support**: Monitor 100+ county jails across the United States
- **Real-time Notifications**: Receive alerts when monitored individuals are arrested or released
- **Modern Web Interface**: React-based frontend with responsive design
- **REST API**: Full-featured API for integration with other systems
- **User Management**: Multi-user support with role-based access control and aMember integration
- **Advanced Search**: Search inmates across all monitored jails with filtering
- **Days Incarcerated Tracking**: Automatic calculation of incarceration duration
- **Mugshot Support**: Automatic fetching and display of inmate photos
- **Performance Optimized**: Asynchronous processing for faster scraping
- **Database Agnostic**: Supports MySQL, PostgreSQL, and SQLite
- **Automatic Migrations**: Database schema updates run automatically on deployment

## 🏗️ Project Architecture

- **`backend/`** - Python FastAPI backend with scraping engine and web API
- **`frontend/`** - React/TypeScript web interface with modern design
- **`amember-plugin/`** - PHP plugin for aMember integration
- **Database-agnostic design** - Works with MySQL, PostgreSQL, SQLite

### 🐳 Docker Images

The project consists of three optimized Docker images:

- **`justinkumpe/incarceration_bot`** - Core scraping service (backend only)
- **`justinkumpe/incarceration_bot_api`** - FastAPI web service with automatic migrations
- **`justinkumpe/incarceration_bot_frontend`** - React web interface

## 🚀 Quick Start

### Full Stack Deployment (Recommended)

1. **Clone the repository:**

   ```bash
   git clone https://github.com/kumpeapps/incarceration_bot.git
   cd incarceration_bot
   ```

2. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env with your database and notification settings
   ```

3. **Start all services:**

   ```bash
   # For development (local build)
   docker-compose up -d
   
   # For production (pre-built images)
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Access the application:**
   - **Web Interface**: <http://localhost:3000>
   - **API Documentation**: <http://localhost:8000/docs>
   - **Database Admin**: <http://localhost:8080> (if enabled)

5. **Default credentials:**
   - **Admin**: `admin` / `admin123`
   - **User**: `user` / `user123`

### Backend Only Deployment

For headless operation without the web interface:

```bash
docker-compose -f docker-compose.yml.example up -d
```

## 🎨 Web Interface Features

The modern React-based interface provides comprehensive jail monitoring capabilities:

### 📊 Dashboard

- Real-time system statistics and activity overview
- Recent arrests and releases summary
- Monitor status and notification history
- System health indicators

### 🔍 Inmate Search & Management

- **Advanced Search**: Search across all monitored jails with multiple filters
- **Detailed View**: Complete inmate information including charges, dates, and mugshots
- **Days Incarcerated**: Automatic calculation of incarceration duration
- **Status Tracking**: Real-time custody status with release date management
- **Booking History**: Track multiple incarcerations for the same individual

### 🔔 Monitor Management

- **Personal Monitors**: Add and manage arrest notifications for specific individuals
- **Multi-User Support**: Each user maintains their own monitor list
- **Notification Settings**: Configure Pushover alerts with custom priorities
- **Real-time Updates**: Instant notifications when monitored individuals are arrested

### 👥 User Management

- **Role-Based Access**: Admin and standard user roles
- **Secure Authentication**: JWT-based session management
- **User Profiles**: Manage notification preferences and settings

### 🏢 Jail Management

- **Jail Directory**: View all supported jails with status indicators
- **Configuration**: Enable/disable specific jails for monitoring
- **Performance Metrics**: Track scraping success rates and timing

## ⚡ Technical Features & Optimizations

### 🔄 Asynchronous Processing

- **Concurrent HTTP Requests**: Utilizes `aiohttp` for parallel web scraping
- **Connection Pooling**: Reuses connections for improved performance
- **Rate Limiting**: Configurable concurrency to prevent server overload
- **Fallback Support**: Graceful degradation to synchronous processing when needed

### 🔔 Advanced Notification System

- **Multi-User Support**: Fixed critical bug where only the first user received notifications
- **Duplicate Prevention**: Smart filtering prevents spam notifications
- **Pushover Integration**: Rich notifications with custom priorities and sounds
- **Webhook Support**: Heartbeat monitoring and custom webhook integrations

### 📊 Data Management

- **Intelligent Release Detection**: Uses `(name, arrest_date)` tuples for accurate tracking
- **Automatic Date Calculations**: Real-time incarceration duration tracking
- **Status Consistency**: Unified status logic across all interfaces
- **Database Optimization**: Efficient queries and connection management

### 🖼️ Image Processing

- **Async Mugshot Fetching**: Parallel image downloads with timeout controls
- **Automatic Retry Logic**: Handles failed downloads gracefully
- **Storage Optimization**: Efficient image storage and retrieval

### 🐳 Deployment Features

- **Multi-Stage Docker Builds**: Optimized images for production deployment
- **Environment Flexibility**: Support for development, staging, and production configs
- **Health Monitoring**: Built-in health checks and status monitoring
- **Maintenance Mode**: Graceful service maintenance with user notifications

## 🏛️ Supported Jails

### 100+ County Jails Across the United States

We continuously expand our jail coverage. If your county uses the Zuercher portal, it can be added quickly to our `jails.json` database. For other jail systems, custom scraping implementation may be required.

**📝 Request Additional Jails**: Submit an issue or pull request to add your county jail.

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

## 📋 Configuration & Environment Variables

The system supports extensive configuration through environment variables:

### Core Database Settings

```bash
# Database Connection (choose one method)
DATABASE_URI=mysql://user:password@host:port/database  # Direct URI
# OR
MYSQL_SERVER=localhost
MYSQL_USERNAME=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=incarceration_bot
MYSQL_PORT=3306
```

### Notification Settings

```bash
# Pushover Integration
PUSHOVER_API_KEY=your_pushover_api_key
PUSHOVER_PRIORITY=1                    # -2 to 2 (2 = emergency)
PUSHOVER_SOUND=pushover               # Sound name for notifications

# Webhook Integration
HEARTBEAT_WEBHOOK=https://your-webhook-url.com/endpoint
```

### Operational Settings

```bash
# Timezone
TZ=America/Chicago                    # Defaults to UTC

# Scheduling
RUN_SCHEDULE=01:00,05:00,09:00,13:00,17:00,21:00  # 24-hour format
ON_DEMAND=False                       # Set True for immediate execution

# Jail Filtering
ENABLE_JAILS_CONTAINING=ar,tx         # Enable jails containing these strings

# Image Processing
FETCH_MUGSHOTS=True                   # Enable mugshot downloading
MUGSHOT_TIMEOUT=5                     # Timeout in seconds
```

### API & Security Settings

```bash
# JWT Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Settings
FRONTEND_URL=http://localhost:3000    # For development
```

## 🚢 Deployment Options

### Development Environment

```bash
# Clone and setup
git clone https://github.com/kumpeapps/incarceration_bot.git
cd incarceration_bot
cp .env.example .env

# Start with local builds
docker-compose up -d
```

### Production Deployment

```bash
# Use pre-built production images
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Beta/Staging Environment

```bash
# Use beta images for testing
docker-compose -f docker-compose.beta.yml --env-file .env.beta up -d
```

### Headless Backend Only

For automated monitoring without the web interface:

```bash
# Backend scraper only
docker-compose -f docker-compose.yml.example up -d
```

## 🔧 Maintenance & Monitoring

### Health Checks

All services include built-in health monitoring:

- **Backend API**: `GET /health`
- **Database**: Connection status checks
- **Scraper**: Heartbeat webhook integration

### Maintenance Mode

```bash
# Enable maintenance mode
docker exec incarceration_bot python maintenance_mode.py --enable

# Disable maintenance mode  
docker exec incarceration_bot python maintenance_mode.py --disable
```

### Database Management

```bash
# Initialize database
docker exec incarceration_bot python init_db.py

# Run migrations
docker exec incarceration_bot alembic upgrade head

# Create admin user
docker exec incarceration_bot python create_admin.py
```

## 📊 Performance & Optimization

The system includes several performance optimizations:

- **Asynchronous scraping** for faster data collection
- **Connection pooling** for database efficiency  
- **Intelligent caching** to reduce redundant requests
- **Optimized Docker images** with multi-stage builds
- **Rate limiting** to prevent server overload
- **Background processing** for non-blocking operations

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Adding New Jails

- **Zuercher-based jails**: Add to `backend/jails.json`
- **Custom scraping**: Implement in `backend/scrapes/`
- **Submit issues** for jail requests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **GitHub Issues**: [Report bugs](https://github.com/kumpeapps/incarceration_bot/issues)
- **Discussions**: [Ask questions](https://github.com/kumpeapps/incarceration_bot/discussions)  
- **Documentation**: Check the `/docs` folder for detailed guides

---

**⭐ Star this repository if you find it useful!**
