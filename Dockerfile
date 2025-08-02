# PayKript Backend Dockerfile
FROM python:3.9-slim

# Sistem paketlerini güncelle ve gerekli bağımlılıkları yükle
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini oluştur
WORKDIR /app

# Python requirements'ı kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodlarını kopyala
COPY backend/ ./backend/
COPY start.py .

# Port açma (Railway dinamik port atar)
EXPOSE 8000

# Sağlık kontrolü (Railway kendi health check'ini yapar)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Non-root kullanıcı oluştur
RUN useradd --create-home --shell /bin/bash paykript
RUN chown -R paykript:paykript /app
USER paykript

# Uygulamayı başlat
CMD ["python", "start.py"] 