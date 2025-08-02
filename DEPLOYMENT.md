# 🚂 PayKript Railway Deployment Guide

PayKript'i Railway.app üzerinden production'a deploy etmek için adım adım rehber.

## 📋 Ön Gereksinimler

1. [Railway.app](https://railway.app) hesabı
2. GitHub repository (✅ Hazır: https://github.com/sukruuzun/PayKript)
3. TronGrid API Key ([trongrid.io](https://trongrid.io)'dan ücretsiz alın)

## 🚀 Deployment Adımları

### 1. Railway CLI Kurulumu

```bash
# npm ile kurulum
npm install -g @railway/cli

# Veya curl ile
curl -fsSL https://railway.app/install.sh | sh
```

### 2. Railway'e Login

```bash
railway login
```

### 3. Yeni Proje Oluşturma

```bash
# Proje dizininde
cd PayKript
railway init

# Proje ismini ayarlayın: "paykript" veya "paykript-production"
```

### 4. PostgreSQL Database Ekleme

```bash
# PostgreSQL addon ekle
railway add postgresql

# Database bilgilerini görmek için
railway variables
```

### 5. Environment Variables Ayarlama

Railway dashboard'dan veya CLI ile environment variables ekleyin:

```bash
# Güvenlik
railway variables set SECRET_KEY="your-very-secure-production-secret-key-at-least-32-chars"
railway variables set ALGORITHM="HS256"
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES="60"

# TRON Blockchain
railway variables set TRON_GRID_API_KEY="your-trongrid-api-key"
railway variables set TRON_NETWORK="mainnet"

# Environment
railway variables set ENVIRONMENT="production"
railway variables set LOG_LEVEL="INFO"

# Webhook Security
railway variables set WEBHOOK_SECRET="your-webhook-secret-key"

# CORS Origins (kendi domain'lerinizi ekleyin)
railway variables set ALLOWED_ORIGINS="https://your-domain.com,https://api.your-domain.com"

# Payment Settings
railway variables set PAYMENT_TIMEOUT_MINUTES="15"
railway variables set REQUIRED_CONFIRMATIONS="1"

# USDT Contract (Mainnet)
railway variables set USDT_CONTRACT_ADDRESS="TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
```

### 6. Deploy

```bash
# GitHub'dan deploy (önerilen)
railway up

# Veya local'den deploy
railway deploy
```

## 🔧 Konfigürasyon Detayları

### Database URL

Railway otomatik olarak `DATABASE_URL` environment variable'ı oluşturacak. Formatı:
```
postgresql://user:password@host:port/database
```

### Redis (Opsiyonel)

```bash
# Redis addon ekle (Celery için)
railway add redis
```

### Custom Domain

1. Railway dashboard'a gidin
2. Settings > Domains
3. Custom domain ekleyin
4. DNS ayarlarını yapın

## 📊 Monitoring ve Logs

```bash
# Logs görüntüle
railway logs

# Metrics görüntüle  
railway status

# Variables kontrol et
railway variables
```

## 🔐 Güvenlik Kontrol Listesi

- [ ] `SECRET_KEY` güçlü ve unique (en az 32 karakter)
- [ ] `WEBHOOK_SECRET` güçlü ve unique
- [ ] `TRON_GRID_API_KEY` production key
- [ ] `ALLOWED_ORIGINS` sadece gerçek domain'ler
- [ ] `ENVIRONMENT=production`
- [ ] Database güvenlik ayarları

## 🌐 Production Checklist

- [ ] TronGrid API key limitleri kontrol edildi
- [ ] Database backup stratejisi planlandı
- [ ] Monitoring/alerting ayarlandı
- [ ] Custom domain konfigüre edildi
- [ ] SSL sertifikası aktif
- [ ] Rate limiting ayarları kontrol edildi

## 🔄 Continuous Deployment

Railway otomatik olarak GitHub'daki değişiklikleri deploy eder:

1. GitHub'a push yapın
2. Railway otomatik build başlatır
3. Health check geçerse live'a alır
4. Başarısız olursa rollback yapar

## 🆘 Troubleshooting

### Build Hatası
```bash
# Build logs kontrol et
railway logs --build

# Local'de test et
docker build -t paykript .
docker run -p 8000:8000 paykript
```

### Database Bağlantı Hatası
```bash
# Database variables kontrol et
railway variables | grep DATABASE

# Database durumu kontrol et
railway status
```

### Health Check Hatası
```bash
# App logs kontrol et
railway logs

# Health endpoint test et
curl https://your-app.railway.app/health
```

## 📞 Destek

- Railway Documentation: https://docs.railway.app
- PayKript GitHub Issues: https://github.com/sukruuzun/PayKript/issues
- TronGrid API Docs: https://developers.tron.network

## 🎯 Sonraki Adımlar

1. WordPress eklentisinde API URL'yi production URL ile değiştirin
2. Webhook URL'lerini test edin
3. Payment flow'unu test edin
4. Monitoring dashboard'ları kurun

---

**PayKript artık Railway'de live! 🚀**

Production URL: `https://your-app.railway.app`
Health Check: `https://your-app.railway.app/health`
API Docs: `https://your-app.railway.app/api/v1/docs` 