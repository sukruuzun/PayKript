from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.db.models import User
from app.schemas.user import UserCreate, User as UserSchema, UserLogin, Token, UserUpdate

router = APIRouter()

@router.post("/kayit", response_model=UserSchema, summary="Yeni kullanıcı kaydı")
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Yeni satıcı hesabı oluştur
    """
    # Email zaten kullanılıyor mu kontrol et
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi zaten kullanılıyor"
        )
    
    # Yeni kullanıcı oluştur
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        company_name=user_data.company_name,
        phone=user_data.phone,
        is_active=True,
        is_verified=False  # Email doğrulama eklenebilir
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/giris", response_model=Token, summary="Kullanıcı girişi")
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Email ve şifre ile giriş yap
    """
    # Kullanıcıyı bul
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı"
        )
    
    # Şifreyi kontrol et
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı"
        )
    
    # Hesap aktif mi kontrol et
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesap deaktif edilmiş"
        )
    
    # JWT token oluştur
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/giris-form", response_model=Token, summary="Form ile giriş")
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 form ile giriş (username alanına email girilir)
    """
    # Kullanıcıyı bul (username alanına email girilir)
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Şifreyi kontrol et
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-posta veya şifre hatalı",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Hesap aktif mi kontrol et
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hesap deaktif edilmiş"
        )
    
    # JWT token oluştur
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/profil", response_model=UserSchema, summary="Kullanıcı profili")
async def get_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Giriş yapmış kullanıcının profil bilgilerini al
    """
    return current_user

@router.put("/profil", response_model=UserSchema, summary="Profil güncelle")
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcı profil bilgilerini güncelle
    """
    # Güncelleme verilerini uygula
    update_data = user_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.post("/sifre-degistir", summary="Şifre değiştir")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcı şifresini değiştir
    """
    # Mevcut şifreyi doğrula
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mevcut şifre hatalı"
        )
    
    # Yeni şifre kontrolü
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yeni şifre en az 8 karakter olmalıdır"
        )
    
    # Şifreyi güncelle
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Şifre başarıyla değiştirildi"}

@router.post("/token-kontrol", summary="Token geçerliliği kontrol")
async def verify_token_endpoint(
    current_user: User = Depends(get_current_active_user)
):
    """
    JWT token'ın geçerliliğini kontrol et
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active
    } 