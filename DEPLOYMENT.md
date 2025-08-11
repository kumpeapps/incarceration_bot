# Docker Deployment Guide

This project provides multiple deployment options using Docker images published to Docker Hub.

## Available Images

The project consists of three Docker images:

1. **`justinkumpe/incarceration_bot`** - Backend scraper service
2. **`justinkumpe/incarceration_bot_api`** - API service 
3. **`justinkumpe/incarceration_bot_frontend`** - Frontend web interface

## Deployment Options

### Development (Local Build)
Use the standard `docker-compose.yml` for local development with build contexts:
```bash
docker-compose up -d
```

### Beta Testing
Use pre-built beta images from Docker Hub:
```bash
docker-compose -f docker-compose.beta.yml up -d
```

### Production
Use stable production images from Docker Hub:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Configuration

### Environment Variables
Copy the example environment file and customize for your deployment:
```bash
cp .env.prod.example .env.prod
```

Edit `.env.prod` with your database credentials and configuration.

### Using Environment File
```bash
# For beta deployment
docker-compose -f docker-compose.beta.yml --env-file .env.prod up -d

# For production deployment
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

## Image Tags

- **Latest**: `latest` (stable production)
- **Beta**: `latest-beta` (testing/development)
- **Releases**: Tagged with version numbers (e.g., `v1.0.0`)

## Services

### Backend Scraper (`incarceration_bot`)
- Scrapes jail data according to schedule
- Processes and stores inmate information
- Handles automated release date updates

### API Service (`backend_api`)
- REST API for data access
- Authentication and authorization
- Database operations

### Frontend (`frontend`)
- React-based web dashboard
- Real-time data visualization
- User management interface

## Ports

- **Frontend**: 3000 (configurable via `FRONTEND_PORT`)
- **API**: 8000 (configurable via `API_PORT`)

## Database Requirements

The application requires a MySQL database. Configure connection details in your environment file:

```env
DB_HOST=your-database-host
DB_PORT=3306
DB_USER=your-username
DB_PASSWORD=your-password
DB_NAME=your-database-name
```

## GitHub Actions

The project automatically builds and pushes Docker images:

- **Beta Branch**: Pushes images with `latest-beta` tag
- **Master Branch**: Pushes images with `latest` tag  
- **Releases**: Pushes images with version tags

## Quick Start

1. Clone the repository
2. Copy and configure environment file:
   ```bash
   cp .env.prod.example .env.prod
   # Edit .env.prod with your settings
   ```
3. Deploy with production images:
   ```bash
   docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
   ```
4. Access the dashboard at `http://localhost:3000`

## Updates

To update to the latest images:
```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```
