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

# Database initialization (including migrations) is handled by init_db.py
echo "Database initialization and migrations completed via init_db.py"

# Start the API server
echo "Starting API server..."
exec uvicorn api:app --host 0.0.0.0 --port 8000
