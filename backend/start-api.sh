#!/bin/bash
# Startup script for the Incarceration Bot API

echo "Starting Incarceration Bot API..."

# Run database migrations if needed
# python -c "from database_connect import create_tables; create_tables()"

# Start the FastAPI server
exec uvicorn api:app --host 0.0.0.0 --port 8000 --reload
