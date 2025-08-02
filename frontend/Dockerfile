# PayKript Frontend Dockerfile - Optimized version
FROM nginx:alpine

# Metadata
LABEL maintainer="PayKript Team"
LABEL description="PayKript Frontend - Merchant Dashboard"

# Copy only required files to avoid conflicts
# Step 1: Copy main HTML file
COPY index.html /usr/share/nginx/html/

# Step 2: Copy assets directory (CSS, JS, images)
COPY assets /usr/share/nginx/html/assets

# Step 3: Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port (Railway handles this automatically)
EXPOSE 80

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Start nginx server
CMD ["nginx", "-g", "daemon off;"] 