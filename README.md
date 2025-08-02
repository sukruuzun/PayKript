# PayKript - Kripto Ödeme Doğrulama Platformu

PayKript, e-ticaret siteleri ve freelancer'lar için kripto para (USDT-TRC20) ile güvenli ödeme alma hizmeti sunan bir platformdur.

## 🚀 Özellikler

- **Non-Custodial**: Paranıza asla dokunmayız, sadece ödemeleri doğrularız
- **xPub Tabanlı**: Her sipariş için benzersiz adres üretimi
- **TRON (TRC-20) Desteği**: Düşük işlem ücretleri ile USDT ödemeleri
- **WordPress Entegrasyonu**: WooCommerce eklentisi ile kolay kurulum
- **Gerçek Zamanlı İzleme**: Blockchain üzerinde otomatik ödeme takibi
- **Webhook Bildirimleri**: Ödeme onaylandığında otomatik bildirim

## 📋 Sistem Gereksinimleri

- Python 3.8+
- PostgreSQL 12+
- Redis 6+ (Celery background tasks için)
- Node.js 16+ (Frontend için)

## 🛠️ Kurulum

### 1. Repository'yi Klonlayın

```bash
git clone <repository-url>
cd PayKript
```

### 2. Python Sanal Ortamı Oluşturun

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate     # Windows
```

### 3. Python Paketlerini Yükleyin

```bash
pip install -r requirements.txt
```

### 4. Environment Değişkenlerini Ayarlayın

`env.example` dosyasını `.env` olarak kopyalayın ve düzenleyin:

```bash
cp env.example .env
```

`.env` dosyasında şu değerleri güncelleyin:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/paykript

# Security (güvenli bir anahtar oluşturun)
SECRET_KEY=your-very-secure-secret-key-here

# TRON Blockchain
TRON_GRID_API_KEY=your-trongrid-api-key

# Redis
REDIS_URL=redis://localhost:6379/0

# Webhook
WEBHOOK_SECRET=your-webhook-secret-key
```

### 5. Veritabanını Hazırlayın

PostgreSQL'de veritabanı oluşturun:

```sql
CREATE DATABASE paykript;
CREATE USER paykript_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE paykript TO paykript_user;
```

### 6. Uygulamayı Başlatın

```bash
cd backend
python main.py
```

API şu adreste çalışacak: `http://localhost:8000`

## 📚 API Dokümantasyonu

Uygulama çalışırken şu adreslerde API dokümantasyonuna erişebilirsiniz:

- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`

## 🔧 API Kullanımı

### 1. Kullanıcı Kaydı

```bash
curl -X POST "http://localhost:8000/api/v1/auth/kayit" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123",
    "full_name": "Test User",
    "company_name": "Test Company"
  }'
```

### 2. Giriş Yapma

```bash
curl -X POST "http://localhost:8000/api/v1/auth/giris" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

### 3. Cüzdan Ekleme

```bash
curl -X POST "http://localhost:8000/api/v1/yonetim/cuzdanlar" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_name": "Ana Cüzdan",
    "xpub_key": "xpub6C...",
    "network": "tron"
  }'
```

### 4. API Anahtarı Oluşturma

```bash
curl -X POST "http://localhost:8000/api/v1/yonetim/api-anahtarlari" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key_name": "WordPress Sitesi"
  }'
```

### 5. Ödeme Talebi Oluşturma (API Key ile)

```bash
curl -X POST "http://localhost:8000/api/v1/odemeler/olustur" \
  -H "Authorization: Bearer API_KEY:SECRET_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORDER-123",
    "amount": 100.00,
    "currency": "USDT",
    "webhook_url": "https://yoursite.com/webhook",
    "customer_email": "customer@example.com"
  }'
```

## 🔄 Background Services

### Blockchain Monitoring Servisi

Blockchain'i izleyen servisi çalıştırmak için:

```bash
cd backend
python -c "
import asyncio
from app.services.blockchain import blockchain_monitor
asyncio.run(blockchain_monitor.monitor_pending_payments())
"
```

### Celery Worker (Opsiyonel)

Gelecekte background task'lar için:

```bash
celery -A app.core.celery worker --loglevel=info
```

## 🌐 WordPress Entegrasyonu

### WooCommerce Eklentisi

1. `wordpress-plugin/` klasöründeki eklentiyi WordPress sitenize yükleyin
2. Eklentiyi aktifleştirin
3. PayKript ayarlar sayfasından API bilgilerinizi girin
4. Ödeme yöntemleri arasından "USDT ile Öde" seçeneğini aktifleştirin

### Webhook Endpoint'i

WordPress sitenizde PayKript webhook'larını almak için endpoint oluşturun:

```php
// wp-content/themes/your-theme/functions.php veya eklenti içinde

add_action('rest_api_init', function () {
    register_rest_route('paykript/v1', '/webhook', array(
        'methods' => 'POST',
        'callback' => 'handle_paykript_webhook',
        'permission_callback' => '__return_true'
    ));
});

function handle_paykript_webhook($request) {
    $body = $request->get_body();
    $signature = $request->get_header('X-PayKript-Signature');
    
    // Signature doğrulama
    $expected_signature = 'sha256=' . hash_hmac('sha256', $body, WEBHOOK_SECRET);
    
    if (!hash_equals($signature, $expected_signature)) {
        return new WP_Error('invalid_signature', 'Invalid signature', ['status' => 401]);
    }
    
    $data = json_decode($body, true);
    
    if ($data['event'] === 'payment.confirmed') {
        $order_id = $data['data']['order_id'];
        $order = wc_get_order($order_id);
        
        if ($order) {
            $order->payment_complete();
            $order->add_order_note('USDT ödemesi onaylandı: ' . $data['data']['transaction']['tx_hash']);
        }
    }
    
    return ['status' => 'success'];
}
```

## 🔐 Güvenlik

### xPub Anahtarı Güvenliği

- xPub anahtarınız hiçbir zaman private key'inizi ifşa etmez
- Her ödeme için yeni bir adres türetilir
- Adresler deterministik olarak oluşturulur

### API Güvenlik

- Tüm API çağrıları HTTPS üzerinden yapılmalıdır
- API anahtarları güvenli bir şekilde saklanmalıdır
- Webhook imzaları her zaman doğrulanmalıdır

### Webhook Güvenlik

```php
// Webhook imza doğrulama örneği
function verify_webhook_signature($payload, $signature, $secret) {
    $expected_signature = 'sha256=' . hash_hmac('sha256', $payload, $secret);
    return hash_equals($signature, $expected_signature);
}
```

## 📊 İzleme ve Loglama

### Log Seviyeleri

- `DEBUG`: Geliştirme aşamasında detaylı loglar
- `INFO`: Normal operasyon logları
- `WARNING`: Dikkat gerektiren durumlar
- `ERROR`: Hata durumları

### Monitoring

PayKript şu metrikleri takip eder:

- Toplam ödeme sayısı
- Başarılı/başarısız ödeme oranları
- Ortalama onay süreleri
- API kullanım istatistikleri

## 🧪 Test

### Unit Testler

```bash
cd backend
python -m pytest tests/
```

### API Testleri

```bash
# Postman collection'ı kullanın veya
curl testleri çalıştırın
```

## 🚀 Production Deployment

### Docker ile Deployment

```dockerfile
# Dockerfile örneği
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables (Production)

```env
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@db-host:5432/paykript
TRON_GRID_API_KEY=your-production-api-key
SECRET_KEY=very-secure-production-key
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
```

## 📞 Destek

Herhangi bir sorun yaşarsanız:

1. [Issues](../../issues) sayfasından yeni bir issue açın
2. Detaylı hata açıklaması ve logları paylaşın
3. Kullandığınız Python ve sistem versiyonunu belirtin

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🤝 Katkıda Bulunma

1. Repository'yi fork edin
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Branch'i push edin (`git push origin feature/AmazingFeature`)
5. Pull Request oluşturun

## 📈 Roadmap

- [ ] Ethereum (ERC-20) desteği
- [ ] Bitcoin Lightning Network entegrasyonu
- [ ] Shopify eklentisi
- [ ] Mobil uygulama
- [ ] Multi-signature wallet desteği
- [ ] Otomatik fon toplama özelliği

---

**PayKript** - Kripto ödemelerinizi güvenli ve kolay hale getirin! 🚀 