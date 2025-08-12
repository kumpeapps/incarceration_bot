#!/bin/bash
# Quick test to check if the remote image has the new runtime config system

echo "Testing if Harbor registry has updated frontend image..."

# Pull and test the image
docker pull harbor.vm.kumpeapps.com/docker/justinkumpe/incarceration_bot_frontend:latest

# Check if generate-config.sh exists in the image
echo "Checking for generate-config.sh in image..."
docker run --rm harbor.vm.kumpeapps.com/docker/justinkumpe/incarceration_bot_frontend:latest ls -la /docker-entrypoint.d/ | grep generate-config

if [ $? -eq 0 ]; then
    echo "✅ Image has been updated with runtime config system"
    
    # Test with environment variables
    echo "Testing runtime config generation..."
    CONTAINER_ID=$(docker run -d -e VITE_API_BASE_URL=https://test.example.com -e VITE_APP_TITLE="Test Title" harbor.vm.kumpeapps.com/docker/justinkumpe/incarceration_bot_frontend:latest)
    
    # Wait a moment for startup
    sleep 3
    
    echo "Generated config.js:"
    docker exec $CONTAINER_ID cat /usr/share/nginx/html/config.js
    
    # Cleanup
    docker stop $CONTAINER_ID > /dev/null
    
else
    echo "❌ Image does NOT have the updated runtime config system"
    echo "The GitHub Actions build may have failed or not completed yet"
fi
