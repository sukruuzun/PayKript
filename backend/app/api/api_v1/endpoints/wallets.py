from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.db.models import User, MerchantWallet, APIKey
from app.schemas.payment import WalletCreate, WalletResponse, APIKeyCreate, APIKeyResponse, APIKeyList
from app.services.crypto import CryptoService
from app.core.security import generate_api_key, generate_secret_key, get_password_hash

router = APIRouter()

# Cüzdan İşlemleri
@router.post("/cuzdanlar", response_model=WalletResponse, summary="Yeni cüzdan ekle")
async def create_wallet(
    wallet_data: WalletCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Yeni cüzdan (xPub anahtarı) ekle
    """
    # xPub anahtarının geçerliliğini kontrol et
    if not CryptoService.validate_xpub_key(wallet_data.xpub_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz xPub anahtarı"
        )
    
    # xPub anahtarı zaten kullanılıyor mu kontrol et
    existing_wallet = db.query(MerchantWallet).filter(
        MerchantWallet.xpub_key == wallet_data.xpub_key
    ).first()
    
    if existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu xPub anahtarı zaten kullanılıyor"
        )
    
    # Test adresi oluşturmayı dene
    test_address = CryptoService.derive_address_from_xpub(
        wallet_data.xpub_key, 
        0, 
        wallet_data.derivation_path
    )
    
    if not test_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="xPub anahtarından adres oluşturulamadı"
        )
    
    # Kullanıcının diğer cüzdanlarını deaktif et (tek aktif cüzdan)
    db.query(MerchantWallet).filter(
        MerchantWallet.user_id == current_user.id
    ).update({"is_active": False})
    
    # Yeni cüzdan oluştur
    new_wallet = MerchantWallet(
        user_id=current_user.id,
        wallet_name=wallet_data.wallet_name,
        xpub_key=wallet_data.xpub_key,
        network=wallet_data.network,
        derivation_path=wallet_data.derivation_path,
        is_active=True  # Yeni cüzdan otomatik olarak aktif
    )
    
    db.add(new_wallet)
    db.commit()
    db.refresh(new_wallet)
    
    return new_wallet

@router.get("/cuzdanlar", response_model=List[WalletResponse], summary="Cüzdan listesi")
async def list_wallets(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcının cüzdanlarını listele
    """
    wallets = db.query(MerchantWallet).filter(
        MerchantWallet.user_id == current_user.id
    ).order_by(MerchantWallet.created_at.desc()).all()
    
    return wallets

@router.put("/cuzdanlar/{wallet_id}/aktif", response_model=WalletResponse, summary="Cüzdan aktif et")
async def activate_wallet(
    wallet_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Belirtilen cüzdanı aktif hale getir
    """
    # Cüzdanın kullanıcıya ait olduğunu kontrol et
    wallet = db.query(MerchantWallet).filter(
        MerchantWallet.id == wallet_id,
        MerchantWallet.user_id == current_user.id
    ).first()
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cüzdan bulunamadı"
        )
    
    # Diğer cüzdanları deaktif et
    db.query(MerchantWallet).filter(
        MerchantWallet.user_id == current_user.id
    ).update({"is_active": False})
    
    # Bu cüzdanı aktif et
    wallet.is_active = True
    
    db.commit()
    db.refresh(wallet)
    
    return wallet

@router.delete("/cuzdanlar/{wallet_id}", summary="Cüzdan sil")
async def delete_wallet(
    wallet_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cüzdanı sil (dikkatli kullanın!)
    """
    # Cüzdanın kullanıcıya ait olduğunu kontrol et
    wallet = db.query(MerchantWallet).filter(
        MerchantWallet.id == wallet_id,
        MerchantWallet.user_id == current_user.id
    ).first()
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cüzdan bulunamadı"
        )
    
    # Aktif ödemesi olan cüzdanları silinmesin
    from app.db.models import PaymentRequest, PaymentStatus
    active_payments = db.query(PaymentRequest).filter(
        PaymentRequest.wallet_id == wallet_id,
        PaymentRequest.status == PaymentStatus.PENDING
    ).count()
    
    if active_payments > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aktif ödemesi olan cüzdan silinemez"
        )
    
    db.delete(wallet)
    db.commit()
    
    return {"message": "Cüzdan silindi"}

@router.get("/cuzdanlar/{wallet_id}/test-adres", summary="Test adresi oluştur")
async def generate_test_address(
    wallet_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cüzdan için test adresi oluştur
    """
    # Cüzdanın kullanıcıya ait olduğunu kontrol et
    wallet = db.query(MerchantWallet).filter(
        MerchantWallet.id == wallet_id,
        MerchantWallet.user_id == current_user.id
    ).first()
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cüzdan bulunamadı"
        )
    
    # Test adresi oluştur
    test_address = CryptoService.derive_address_from_xpub(
        wallet.xpub_key, 
        0,  # Test için index 0 kullan
        wallet.derivation_path
    )
    
    if not test_address:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test adresi oluşturulamadı"
        )
    
    return {
        "test_address": test_address,
        "index": 0,
        "derivation_path": wallet.derivation_path,
        "network": wallet.network
    }

# API Anahtarı İşlemleri
@router.post("/api-anahtarlari", response_model=APIKeyResponse, summary="Yeni API anahtarı oluştur")
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Yeni API anahtarı oluştur
    """
    # API anahtarı ve secret oluştur
    api_key = generate_api_key()
    secret_key = generate_secret_key()
    secret_hash = get_password_hash(secret_key)
    
    # API anahtarını veritabanına kaydet
    new_api_key = APIKey(
        user_id=current_user.id,
        key_name=api_key_data.key_name,
        api_key=api_key,
        secret_key=secret_hash,
        is_active=True
    )
    
    db.add(new_api_key)
    db.commit()
    db.refresh(new_api_key)
    
    # Response'da gerçek secret key'i döndür (sadece bu sefer)
    return APIKeyResponse(
        id=new_api_key.id,
        key_name=new_api_key.key_name,
        api_key=new_api_key.api_key,
        secret_key=secret_key,  # Gerçek secret key (sadece oluşturulurken gösterilir)
        is_active=new_api_key.is_active,
        last_used_at=new_api_key.last_used_at,
        created_at=new_api_key.created_at
    )

@router.get("/api-anahtarlari", response_model=List[APIKeyList], summary="API anahtarı listesi")
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcının API anahtarlarını listele
    """
    api_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id
    ).order_by(APIKey.created_at.desc()).all()
    
    return api_keys

@router.put("/api-anahtarlari/{key_id}/durum", summary="API anahtarı durumu değiştir")
async def toggle_api_key_status(
    key_id: int,
    is_active: bool,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    API anahtarını aktif/pasif yap
    """
    # API anahtarının kullanıcıya ait olduğunu kontrol et
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API anahtarı bulunamadı"
        )
    
    api_key.is_active = is_active
    db.commit()
    
    status_text = "aktif" if is_active else "pasif"
    return {"message": f"API anahtarı {status_text} hale getirildi"}

@router.delete("/api-anahtarlari/{key_id}", summary="API anahtarı sil")
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    API anahtarını sil
    """
    # API anahtarının kullanıcıya ait olduğunu kontrol et
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API anahtarı bulunamadı"
        )
    
    db.delete(api_key)
    db.commit()
    
    return {"message": "API anahtarı silindi"} 