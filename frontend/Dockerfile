# PayKript Frontend Dockerfile - Railway Dynamic Port Version
FROM nginx:alpine

# Metadata
LABEL maintainer="PayKript Team"
LABEL description="PayKript Frontend - Railway Dynamic Port Support"

# Copy static files
COPY index.html /usr/share/nginx/html/

# Copy favicon files
COPY favicon.ico /usr/share/nginx/html/
COPY favicon.svg /usr/share/nginx/html/
COPY favicon.png /usr/share/nginx/html/

# Copy assets directory
COPY assets /usr/share/nginx/html/assets/

# Copy the Nginx config template to templates directory
COPY default.conf.template /etc/nginx/templates/default.conf.template

# Copy the startup script and make it executable
COPY start-nginx.sh /start-nginx.sh
RUN chmod +x /start-nginx.sh

# Expose Railway's dynamic port (default fallback)
EXPOSE 8080

# Health check endpoint - uses Railway's dynamic PORT
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Use startup script instead of direct nginx command
CMD ["/start-nginx.sh"] 