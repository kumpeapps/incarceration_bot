#!/bin/bash
# aaPanel Cache Clearing Script for Frontend Files

echo "=== AAPANEL CACHE CLEARING SCRIPT ==="
echo "Run this on your proxy server that has aaPanel"
echo

echo "1. Clear Nginx cache (if using nginx cache module):"
echo "sudo rm -rf /tmp/nginx_cache/*"
echo "sudo rm -rf /var/cache/nginx/*"
echo

echo "2. Clear aaPanel static file cache:"
echo "sudo rm -rf /www/server/panel/static_cache/*"
echo "sudo rm -rf /www/server/panel/cache/*"
echo

echo "3. Clear OpenResty/Nginx cache directories:"
echo "sudo rm -rf /usr/local/openresty/nginx/cache/*"
echo "sudo rm -rf /www/server/nginx/cache/*"
echo

echo "4. Clear potential reverse proxy cache:"
echo "sudo rm -rf /tmp/proxy_cache/*"
echo "sudo rm -rf /var/cache/proxy/*"
echo

echo "5. Restart services:"
echo "sudo systemctl reload nginx"
echo "sudo systemctl restart nginx"
echo

echo "6. If using OpenResty:"
echo "sudo systemctl reload openresty"
echo "sudo systemctl restart openresty"
echo

echo "7. Check for any fastcgi_cache:"
echo "sudo find /tmp -name '*fastcgi*' -type d"
echo "sudo find /var/cache -name '*fastcgi*' -type d"
echo

echo "8. Manual cache location check:"
echo "sudo find /www -name '*cache*' -type d | grep -v '.cache'"
echo

echo "=== AAPANEL SPECIFIC COMMANDS ==="
echo "9. aaPanel cache clear via CLI (if available):"
echo "cd /www/server/panel && python tools.py cache_clear"
echo

echo "10. Check aaPanel site configuration for caching directives:"
echo "cat /www/server/panel/vhost/nginx/YOURDOMAIN.conf | grep -i cache"
echo

echo "=== NUCLEAR OPTION ==="
echo "11. If nothing else works, temporarily change backend to a different port:"
echo "# In your proxy config, change from localhost:3000 to localhost:3001"
echo "# Start container on port 3001 to bypass any hardcoded cache"
echo

echo "Run these commands on your proxy server to clear all possible caches."
