#!/bin/sh
# PayKript Frontend - Dynamic Port Nginx Startup Script
# This script configures Nginx to use Railway's dynamic PORT

echo "🚀 PayKript Frontend Starting..."
echo "📡 Railway assigned PORT: ${PORT:-8080}"

# Substitute the ${PORT} variable in the Nginx config template
# with the actual port number provided by Railway
envsubst '${PORT}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "✅ Nginx configuration generated:"
cat /etc/nginx/conf.d/default.conf

echo "🌐 Starting Nginx on port ${PORT:-8080}..."

# Start Nginx in the foreground (required for Docker)
nginx -g 'daemon off;' 