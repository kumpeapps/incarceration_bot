#!/bin/sh
# Generate runtime configuration from environment variables
# Supports both API_BASE_URL/VITE_API_BASE_URL and APP_TITLE/VITE_APP_TITLE

# Use API_BASE_URL or VITE_API_BASE_URL, with fallback
API_URL="${API_BASE_URL:-${VITE_API_BASE_URL:-http://localhost:8000}}"
APP_NAME="${APP_TITLE:-${VITE_APP_TITLE:-Incarceration Bot Dashboard}}"

# Generate the config.js file
cat > /usr/share/nginx/html/config.js << EOF
window.runtimeConfig = {
  API_BASE_URL: "${API_URL}",
  APP_TITLE: "${APP_NAME}"
};
EOF

echo "Runtime config generated:"
echo "  API_BASE_URL: ${API_URL}"
echo "  APP_TITLE: ${APP_NAME}"
