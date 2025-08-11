# Build stage
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Install envsubst (gettext package) for environment variable substitution
RUN apk add --no-cache gettext

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the runtime config generation script
COPY generate-config.sh /docker-entrypoint.d/10-generate-config.sh
RUN chmod +x /docker-entrypoint.d/10-generate-config.sh

# Expose port 80
EXPOSE 80

# Start nginx (the entrypoint script will run automatically)
CMD ["nginx", "-g", "daemon off;"]
