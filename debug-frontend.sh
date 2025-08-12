#!/bin/bash
# Debug script for frontend runtime configuration issues

echo "=== FRONTEND CONFIGURATION DEBUG ==="
echo "Date: $(date)"
echo

echo "1. Checking Docker container status..."
docker ps | grep frontend
echo

echo "2. Checking environment variables in container..."
CONTAINER_ID=$(docker ps -q --filter "name=frontend")
if [ -n "$CONTAINER_ID" ]; then
    echo "Container ID: $CONTAINER_ID"
    docker exec $CONTAINER_ID env | grep -E "(API_BASE_URL|APP_TITLE|VITE_)" || echo "No API/TITLE env vars found"
else
    echo "No frontend container found!"
fi
echo

echo "3. Checking if generate-config.sh exists..."
if [ -n "$CONTAINER_ID" ]; then
    docker exec $CONTAINER_ID ls -la /docker-entrypoint.d/ | grep generate-config || echo "generate-config.sh NOT FOUND"
    echo
    echo "4. Checking generate-config.sh content..."
    docker exec $CONTAINER_ID cat /docker-entrypoint.d/10-generate-config.sh 2>/dev/null || echo "Cannot read generate-config.sh"
else
    echo "Cannot check - no container running"
fi
echo

echo "5. Checking current config.js content..."
if [ -n "$CONTAINER_ID" ]; then
    docker exec $CONTAINER_ID cat /usr/share/nginx/html/config.js 2>/dev/null || echo "Cannot read config.js"
else
    echo "Cannot check - no container running"
fi
echo

echo "6. Checking container logs for runtime config generation..."
if [ -n "$CONTAINER_ID" ]; then
    docker logs $CONTAINER_ID 2>&1 | grep -A3 -B3 "Runtime config\|generate-config" || echo "No runtime config logs found"
else
    echo "Cannot check - no container running"
fi
echo

echo "7. Checking image creation date..."
docker inspect harbor.vm.kumpeapps.com/docker/justinkumpe/incarceration_bot_frontend:latest | grep Created || echo "Cannot inspect image"
echo

echo "=== DEBUG COMPLETE ==="
