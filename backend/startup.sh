#!/bin/bash
set -e

echo "Starting incarceration_bot API container..."

# Run database initialization
echo "Initializing database..."
python /app/init_db.py

# Check if initialization was successful
if [ $? -eq 0 ]; then
    echo "Database initialization completed successfully"
else
    echo "Database initialization failed"
    exit 1
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Check if migrations were successful
if [ $? -eq 0 ]; then
    echo "Database migrations completed successfully"
else
    echo "Database migrations failed"
    exit 1
fi

# Start the API server
echo "Starting API server..."
exec uvicorn api:app --host 0.0.0.0 --port 8000
