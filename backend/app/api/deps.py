from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.db.database import SessionLocal
from app.db.models import User, APIKey
from app.core.config import settings
from app.core.security import verify_token, AuthenticationError, verify_api_credentials

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)

def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    JWT token'dan aktif kullanıcıyı al
    """
    if not credentials:
        raise AuthenticationError("Token gereklidir")
    
    # Token'ı doğrula
    payload = verify_token(credentials.credentials)
    if not payload:
        raise AuthenticationError("Geçersiz token")
    
    # Email'i payload'dan al
    email = payload.get("sub")
    if not email:
        raise AuthenticationError("Geçersiz token payload")
    
    # Kullanıcıyı database'den al
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise AuthenticationError("Kullanıcı bulunamadı")
    
    if not user.is_active:
        raise AuthenticationError("Hesap deaktif")
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Aktif kullanıcı kontrolü
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesap deaktif"
        )
    return current_user

async def get_api_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    API Key ile kullanıcı authentication
    WordPress eklentisi için kullanılır
    """
    # Authorization header'ını kontrol et
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationError("API anahtarı gereklidir")
    
    try:
        # Bearer token'ı parse et
        # Format: "Bearer api_key:secret_key"
        token = auth_header.split(" ")[1]
        if ":" not in token:
            raise AuthenticationError("Geçersiz API anahtarı formatı")
        
        api_key, secret_key = token.split(":", 1)
        
    except (IndexError, ValueError):
        raise AuthenticationError("Geçersiz API anahtarı formatı")
    
    # API anahtarını database'den al
    api_key_obj = db.query(APIKey).filter(
        APIKey.api_key == api_key,
        APIKey.is_active == True
    ).first()
    
    if not api_key_obj:
        raise AuthenticationError("Geçersiz API anahtarı")
    
    # Secret key'i doğrula
    if not verify_api_credentials(api_key, secret_key, api_key_obj.api_key, api_key_obj.secret_key_hash):
        raise AuthenticationError("Geçersiz API credentials")
    
    # Kullanıcıyı al
    user = db.query(User).filter(User.id == api_key_obj.user_id).first()
    if not user or not user.is_active:
        raise AuthenticationError("Kullanıcı bulunamadı veya deaktif")
    
    # Last used timestamp'i güncelle
    from datetime import datetime
    api_key_obj.last_used_at = datetime.utcnow()
    db.commit()
    
    return user

def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Admin yetkisi gerektirir
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin yetkisi gereklidir"
        )
    return current_user

async def get_user_from_api_or_jwt(
    request: Request,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> User:
    """
    JWT token veya API key ile authentication
    Hem dashboard hem de API kullanümı için
    """
    # Önce API key kontrolü yap
    auth_header = request.headers.get("Authorization", "")
    
    # API key formatı kontrolü (içinde : varsa API key)
    if ":" in auth_header.replace("Bearer ", ""):
        # API key authentication
        return await get_api_user(request, db)
    else:
        # JWT token authentication
        return await get_current_active_user(await get_current_user(credentials, db))

# Rate limiting için helper
def get_client_ip(request: Request) -> str:
    """
    Client IP adresini al
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown" 