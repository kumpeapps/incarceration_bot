#!/bin/bash
# Local environment setup script
# This sets the same database environment variables as Docker Compose

export DB_HOST=172.16.21.10
export DB_PORT=3306
export DB_USER=jail_test
export DB_PASSWORD=LetmeN2it
export DB_NAME=jail_test
export DB_TYPE=mysql
export TZ=America/Chicago
export ON_DEMAND=True
export ENABLE_JAILS_CONTAINING=so-ar,aiken-so-sc
export LOG_LEVEL=TRACE
export FETCH_MUGSHOTS=True
export MUGSHOT_TIMEOUT=5

echo "🔧 Environment variables set for local development"
echo "🗄️  Database: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo "👤 User: ${DB_USER}"
echo "📊 Log Level: ${LOG_LEVEL}"
echo ""
echo "🚀 Starting Incarceration Bot..."
echo ""

# Run the application with the environment variables
python3 main.py "$@"
