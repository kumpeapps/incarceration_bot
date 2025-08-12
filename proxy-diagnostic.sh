#!/bin/bash
# Diagnostic script to find the source of wrong config.js

echo "=== PROXY CONFIGURATION DIAGNOSTIC ==="
echo "Date: $(date)"
echo

echo "1. Testing direct container access:"
echo "Container config.js:"
ssh -p 8022 172.16.20.20 "docker exec bot-frontend-1 cat /usr/share/nginx/html/config.js" | head -3
echo

echo "2. Testing port 3000 access:"
echo "Port 3000 config.js:"
curl -s http://172.16.20.20:3000/config.js | head -3
echo

echo "3. Testing proxy access:"
echo "Proxy config.js:"
curl -s https://incarcerationbot.vm.kumpeapps.com/config.js | head -3
echo

echo "4. Checking if proxy might be hitting port 8000:"
echo "Port 8000 response:"
curl -s http://172.16.20.20:8000/config.js 2>/dev/null | head -3 || echo "No config.js on port 8000"
echo

echo "5. Testing different potential endpoints:"
for port in 80 8080 8888 3001; do
    echo "Testing port $port:"
    curl -s --connect-timeout 3 http://172.16.20.20:$port/config.js 2>/dev/null | head -3 || echo "Port $port not accessible or no config.js"
    echo
done

echo "6. Checking nginx container for other servers:"
ssh -p 8022 172.16.20.20 "docker ps | grep nginx" || echo "No nginx containers found"
echo

echo "=== DIAGNOSTIC COMPLETE ==="
