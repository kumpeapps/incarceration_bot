# Docker Compose Files

This project provides multiple Docker Compose configurations for different use cases.

## Available Configurations

### `docker-compose.yml` - Local Development
- **Purpose**: Local development with live building
- **Usage**: `docker-compose up -d`
- **Features**:
  - Builds images locally from source code
  - Ideal for development and testing changes
  - Uses local build contexts

### `docker-compose.prod.yml` - Production Deployment
- **Purpose**: Production deployment using stable published images
- **Usage**: `docker-compose -f docker-compose.prod.yml up -d`
- **Features**:
  - Uses `latest` tagged images from Docker Hub
  - Environment variable support
  - Production-optimized settings

### `docker-compose.beta.yml` - Beta Testing
- **Purpose**: Testing with beta/development images
- **Usage**: `docker-compose -f docker-compose.beta.yml up -d`
- **Features**:
  - Uses `latest-beta` tagged images from Docker Hub
  - Latest features and fixes
  - Testing environment

### `docker-compose.yml.example` - Template
- **Purpose**: Template for custom deployments
- **Usage**: Copy and customize for your environment
- **Features**:
  - Shows all available configuration options
  - Includes comments and examples
  - Both image and build options shown

## Environment Configuration

### Using Environment Files
Create a `.env` file for your configuration:

```bash
# Copy from example
cp .env.example .env

# Edit with your settings
nano .env

# Use with compose
docker-compose --env-file .env up -d
```

### Available Environment Files
- **`.env.example`** - Development configuration template
- **`.env.prod.example`** - Production configuration template

## Quick Start Examples

### Development
```bash
# Clone and start development environment
git clone <repository>
cd incarceration_bot
cp .env.example .env
# Edit .env with your database credentials
docker-compose up -d
```

### Production
```bash
# Production deployment with published images
cp .env.prod.example .env.prod
# Edit .env.prod with your production settings
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Beta Testing
```bash
# Test latest beta features
docker-compose -f docker-compose.beta.yml up -d
```

## Services Overview

- **`incarceration_bot`**: Backend scraper service
- **`backend_api`**: REST API service (port 8000)
- **`frontend`**: React web interface (port 3000)

## Migration from Legacy Configuration

If upgrading from an older version:

1. **Database Variables**: New `DB_*` variables replace `MYSQL_*` variables (backward compatible)
2. **Multi-Service**: Now includes separate API and frontend services
3. **Images**: Published images available on Docker Hub

See `DEPLOYMENT.md` for detailed deployment instructions.
