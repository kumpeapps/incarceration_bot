#!/bin/bash
# Quick maintenance command wrapper
# Usage: ./maintenance.sh [command]

cd "$(dirname "$0")"

if [ -z "$1" ]; then
    echo "Usage: ./maintenance.sh [status|populate-last-seen|cleanup-duplicates|quick-cleanup]"
    echo ""
    echo "Available commands:"
    echo "  status              - Check database status"
    echo "  populate-last-seen  - Fix missing last_seen dates"
    echo "  cleanup-duplicates  - Remove duplicates (safe mode)"
    echo "  quick-cleanup       - Remove duplicates (fast mode)"
    echo ""
    echo "For full maintenance mode: ./run_maintenance.sh"
    exit 1
fi

echo "Running maintenance command: $1"
docker-compose exec incarceration_bot python maintenance.py "$1"
