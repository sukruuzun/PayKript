# PayKript Frontend Dockerfile
FROM nginx:alpine

# Maintainer bilgisi
LABEL maintainer="PayKript Team"
LABEL description="PayKript Frontend - Merchant Dashboard"

# Çalışma dizini
WORKDIR /usr/share/nginx/html

# Frontend static dosyalarını kopyala
COPY . /usr/share/nginx/html

# Custom nginx konfigürasyonunu kopyala
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Port bilgisi (Railway otomatik atar)
EXPOSE 80

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Nginx'i başlat
CMD ["nginx", "-g", "daemon off;"] 