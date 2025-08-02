from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import secrets
import string
from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Düz metin şifreyi hash'lenmiş şifre ile karşılaştır
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Şifreyi hash'le
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT access token oluştur
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """
    JWT token'ı doğrula ve payload'ı döndür
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def generate_api_key() -> str:
    """
    Rastgele API anahtarı oluştur
    Format: pk_live_xxxxxxxxxxxxxxxxxxxx (32 karakter)
    """
    prefix = "pk_live_" if settings.ENVIRONMENT == "production" else "pk_test_"
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    return f"{prefix}{random_part}"

def generate_secret_key() -> str:
    """
    Rastgele secret key oluştur
    Format: sk_live_xxxxxxxxxxxxxxxxxxxx (64 karakter)
    """
    prefix = "sk_live_" if settings.ENVIRONMENT == "production" else "sk_test_"
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
    return f"{prefix}{random_part}"

def verify_api_credentials(api_key: str, secret_key: str, stored_api_key: str, stored_secret_hash: str) -> bool:
    """
    API anahtarı ve secret key'i doğrula
    
    Args:
        api_key: Kullanıcının gönderdiği API key (düz text)
        secret_key: Kullanıcının gönderdiği secret key (düz text)
        stored_api_key: Veritabanında saklanan API key (düz text)
        stored_secret_hash: Veritabanında saklanan secret key hash'i
    
    Returns:
        bool: Credentials geçerliyse True
        
    Security Note:
        - API key timing attack'lara karşı secrets.compare_digest kullanır
        - Secret key bcrypt hash ile doğrulanır
    """
    # API key kontrolü - timing attack koruması
    if not secrets.compare_digest(api_key, stored_api_key):
        return False
    
    # Secret key kontrolü - hash karşılaştırma
    return verify_password(secret_key, stored_secret_hash)

def create_webhook_signature(payload: str, secret: str) -> str:
    """
    Webhook için HMAC imzası oluştur
    """
    import hmac
    import hashlib
    
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"sha256={signature}"

def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Webhook imzasını doğrula
    """
    expected_signature = create_webhook_signature(payload, secret)
    return hmac.compare_digest(signature, expected_signature)

# Exception sınıfları
class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Kimlik doğrulama başarısız"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthorizationError(HTTPException):
    def __init__(self, detail: str = "Bu işlem için yetkiniz bulunmuyor"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        ) 