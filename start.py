#!/usr/bin/env python3
"""
PayKript - Kripto Ödeme Doğrulama Platformu
Başlatma scripti
"""

import sys
import asyncio
import uvicorn
import threading
import logging
from pathlib import Path

# Backend dizinini Python path'e ekle
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Logları ayarla
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PayKript")

def start_blockchain_monitor():
    """
    Blockchain monitoring servisini başlat
    """
    try:
        from app.services.blockchain import blockchain_monitor
        
        # Yeni event loop oluştur
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info("🔍 Blockchain monitoring servisi başlatılıyor...")
        loop.run_until_complete(blockchain_monitor.monitor_pending_payments())
        
    except Exception as e:
        logger.error(f"❌ Blockchain monitoring hatası: {e}")

def check_requirements():
    """
    Gerekli bağımlılıkları kontrol et
    """
    try:
        # Backend modules
        from app.core.config import settings
        from app.db.database import engine
        from app.db import models
        
        logger.info("✅ Backend modülleri yüklendi")
        
        # Database bağlantısını test et
        try:
            # Tabloları oluştur
            models.Base.metadata.create_all(bind=engine)
            logger.info("✅ Veritabanı bağlantısı başarılı")
        except Exception as e:
            logger.error(f"❌ Veritabanı hatası: {e}")
            logger.error("💡 PostgreSQL çalıştığından ve .env dosyasının doğru olduğundan emin olun")
            return False
        
        # Environment değişkenlerini kontrol et
        if not settings.SECRET_KEY or settings.SECRET_KEY == "change-this-secret-key-in-production":
            logger.warning("⚠️  SECRET_KEY production için güçlü bir değerle değiştirilmelidir!")
        
        if not settings.TRON_GRID_API_KEY:
            logger.warning("⚠️  TRON_GRID_API_KEY tanımlanmamış. TronGrid API özellikleri çalışmayabilir.")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Eksik paket: {e}")
        logger.error("💡 'pip install -r requirements.txt' komutunu çalıştırın")
        return False
    except Exception as e:
        logger.error(f"❌ Başlatma hatası: {e}")
        return False

def main():
    """
    Ana başlatma fonksiyonu
    """
    print("🚀 PayKript - Kripto Ödeme Doğrulama Platformu")
    print("=" * 50)
    
    # Gereksinimleri kontrol et
    if not check_requirements():
        sys.exit(1)
    
    # Blockchain monitoring'i background thread'de başlat
    monitor_thread = threading.Thread(
        target=start_blockchain_monitor,
        daemon=True,
        name="BlockchainMonitor"
    )
    monitor_thread.start()
    logger.info("🔍 Blockchain monitoring arka planda başlatıldı")
    
    # FastAPI uygulamasını başlat
    import os
    port = int(os.getenv("PORT", 8000))  # Railway $PORT kullan, fallback 8000
    
    logger.info("🌐 FastAPI sunucusu başlatılıyor...")
    logger.info(f"🚀 Port: {port} (Railway: $PORT={os.getenv('PORT', 'not set')})")
    logger.info(f"📚 API Dokümantasyonu: http://localhost:{port}/api/v1/docs")
    logger.info("🛑 Durdurmak için Ctrl+C'ye basın")
    
    try:
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            reload=False,  # Production'da false olmalı
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("👋 PayKript kapatılıyor...")
    except Exception as e:
        logger.error(f"❌ Sunucu hatası: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 