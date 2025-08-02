from typing import List, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

class Settings(BaseSettings):
    # API ayarları
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "PayKript"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/paykript")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 gün
    
    # CORS
    ALLOWED_ORIGINS: List[str] = []
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v) -> List[str]:
        if isinstance(v, str):
            # Gelen metni virgüllerden ayır, boşlukları temizle ve boş elemanları atla
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        # Eğer format beklenmedikse, boş bir liste döndürerek hatayı engelle
        return []
    
    # Environment  
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # TRON Blockchain
    TRON_GRID_API_KEY: str = os.getenv("TRON_GRID_API_KEY", "")
    TRON_NETWORK: str = os.getenv("TRON_NETWORK", "mainnet")  # mainnet or testnet
    TRON_GRID_BASE_URL: str = "https://api.trongrid.io" if os.getenv("TRON_NETWORK", "mainnet") == "mainnet" else "https://api.shasta.trongrid.io"
    
    # Redis (Celery için)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Webhook Security
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "webhook-secret-change-this")
    
    # Ödeme ayarları
    PAYMENT_TIMEOUT_MINUTES: int = 15  # Ödeme için bekleme süresi
    REQUIRED_CONFIRMATIONS: int = 1    # Gerekli blockchain onayı sayısı
    
    # USDT Token Contract Address (TRC-20)
    USDT_CONTRACT_ADDRESS: str = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # Mainnet USDT
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 