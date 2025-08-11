#!/bin/bash

# Maintenance Mode Wrapper Script
# Safely executes maintenance operations in Docker environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==============================================="
echo "    INCARCERATION BOT MAINTENANCE MODE"
echo "==============================================="
echo "This will:"
echo "1. Stop all scraping services"
echo "2. Clean up duplicate records in database"
echo "3. Restart services"
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

# Check if services are running
echo "Checking current service status..."
SERVICES_RUNNING=$(docker-compose ps --services --filter "status=running" | wc -l)
echo "Services currently running: $SERVICES_RUNNING"

# Confirm execution
read -p "Proceed with maintenance mode? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Maintenance cancelled."
    exit 0
fi

echo ""
echo "=== STEP 1: STOPPING SCRAPING SERVICES ==="
echo "Stopping incarceration_bot container..."
if docker-compose stop incarceration_bot; then
    echo "✓ Scraping services stopped successfully"
else
    echo "❌ Failed to stop services"
    exit 1
fi

echo ""
echo "=== STEP 2: DATABASE CLEANUP ==="
echo "Running database cleanup script..."
if docker-compose run --rm incarceration_bot python -c "
from database_connect import new_session
from sqlalchemy import text
try:
    session = new_session()
    session.execute(text('SELECT 1'))
    session.close()
    print('Database connection test successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
"; then
    echo "✓ Database connection confirmed"
else
    echo "❌ Database connection failed"
    exit 1
fi

# Start a temporary container just for cleanup if main container is stopped
echo "Starting temporary container for database cleanup..."
if docker-compose run --rm incarceration_bot python database_cleanup.py; then
    echo "✓ Database cleanup completed successfully"
    CLEANUP_SUCCESS=true
else
    echo "❌ Database cleanup failed"
    CLEANUP_SUCCESS=false
fi

echo ""
echo "=== STEP 3: RESTARTING SERVICES ==="
echo "Restarting incarceration_bot container..."
if docker-compose up -d incarceration_bot; then
    echo "✓ Scraping services restarted successfully"
else
    echo "❌ Failed to restart services"
    exit 1
fi

echo ""
if [ "$CLEANUP_SUCCESS" = true ]; then
    echo "🎉 MAINTENANCE COMPLETED SUCCESSFULLY!"
    echo "   System is back online and ready for normal operations."
    echo "   Check maintenance_cleanup.log for detailed results."
else
    echo "⚠️  MAINTENANCE COMPLETED WITH ISSUES"
    echo "   Services restarted but database cleanup had problems."
    echo "   Check maintenance_cleanup.log for details."
    exit 1
fi
