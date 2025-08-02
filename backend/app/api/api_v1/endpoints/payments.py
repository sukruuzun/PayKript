from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from decimal import Decimal

from app.api.deps import get_db, get_current_active_user, get_api_user
from app.db.models import User, PaymentRequest, MerchantWallet, Transaction, PaymentStatus
from app.schemas.payment import (
    PaymentRequestCreate, PaymentRequestResponse, PaymentRequestDetail,
    TransactionResponse, DashboardStats
)
from app.services.crypto import CryptoService
from app.core.config import settings

router = APIRouter()

@router.post("/olustur", response_model=PaymentRequestResponse, summary="Ödeme talebi oluştur")
async def create_payment_request(
    payment_data: PaymentRequestCreate,
    request: Request,
    current_user: User = Depends(get_api_user),
    db: Session = Depends(get_db)
):
    """
    Yeni ödeme talebi oluştur (WordPress eklentisi için)
    """
    # Kullanıcının aktif cüzdanını al
    wallet = db.query(MerchantWallet).filter(
        MerchantWallet.user_id == current_user.id,
        MerchantWallet.is_active == True
    ).first()
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aktif cüzdan bulunamadı. Lütfen önce bir cüzdan ekleyin."
        )
    
    # Benzersiz adres oluştur
    address_index = wallet.address_index + 1
    try:
        payment_address = CryptoService.derive_address_from_xpub(
            wallet.xpub_key, 
            address_index,
            wallet.derivation_path
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ödeme adresi oluşturulamadı: {str(e)}"
        )
    
    # Ödeme süresini hesapla
    expires_at = datetime.utcnow() + timedelta(minutes=settings.PAYMENT_TIMEOUT_MINUTES)
    
    # Ödeme talebini oluştur
    payment_request = PaymentRequest(
        merchant_id=current_user.id,
        wallet_id=wallet.id,
        order_id=payment_data.order_id,
        amount=payment_data.amount,
        currency=payment_data.currency,
        payment_address=payment_address,
        address_index=address_index,
        expires_at=expires_at,
        webhook_url=payment_data.webhook_url,
        customer_email=payment_data.customer_email,
        customer_info=payment_data.customer_info,
        notes=payment_data.notes
    )
    
    db.add(payment_request)
    
    # Wallet'ın address index'ini güncelle
    wallet.address_index = address_index
    
    db.commit()
    db.refresh(payment_request)
    
    # QR kod oluştur
    qr_code_data = CryptoService.generate_payment_qr(
        payment_address, 
        float(payment_data.amount), 
        payment_data.currency
    )
    
    return PaymentRequestResponse(
        id=payment_request.id,
        order_id=payment_request.order_id,
        amount=payment_request.amount,
        currency=payment_request.currency,
        payment_address=payment_request.payment_address,
        status=payment_request.status,
        expires_at=payment_request.expires_at,
        created_at=payment_request.created_at,
        qr_code_data=qr_code_data
    )

@router.get("/durum/{payment_id}", response_model=PaymentRequestDetail, summary="Ödeme durumu sorgula")
async def get_payment_status(
    payment_id: int,
    current_user: User = Depends(get_api_user),
    db: Session = Depends(get_db)
):
    """
    Ödeme durumunu sorgula (WordPress eklentisi için)
    """
    payment = db.query(PaymentRequest).filter(
        PaymentRequest.id == payment_id,
        PaymentRequest.merchant_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ödeme talebi bulunamadı"
        )
    
    return payment

@router.get("/siparis/{order_id}", response_model=PaymentRequestDetail, summary="Sipariş ID ile ödeme sorgula")
async def get_payment_by_order_id(
    order_id: str,
    current_user: User = Depends(get_api_user),
    db: Session = Depends(get_db)
):
    """
    Sipariş ID'si ile ödeme durumunu sorgula
    """
    payment = db.query(PaymentRequest).filter(
        PaymentRequest.order_id == order_id,
        PaymentRequest.merchant_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sipariş bulunamadı"
        )
    
    return payment

@router.get("/liste", response_model=List[PaymentRequestDetail], summary="Ödeme listesi")
async def list_payments(
    skip: int = Query(0, ge=0, description="Atlanacak kayıt sayısı"),
    limit: int = Query(50, ge=1, le=100, description="Maksimum kayıt sayısı"),
    status_filter: Optional[PaymentStatus] = Query(None, description="Durum filtresi"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Kullanıcının ödeme listesi (Dashboard için)
    """
    query = db.query(PaymentRequest).filter(
        PaymentRequest.merchant_id == current_user.id
    ).options(joinedload(PaymentRequest.transactions))
    
    if status_filter:
        query = query.filter(PaymentRequest.status == status_filter)
    
    payments = query.order_by(PaymentRequest.created_at.desc()).offset(skip).limit(limit).all()
    
    return payments

@router.get("/istatistikler", response_model=DashboardStats, summary="Dashboard istatistikleri")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Dashboard için istatistiksel veriler
    """
    # Toplam ödemeler
    total_payments = db.query(PaymentRequest).filter(
        PaymentRequest.merchant_id == current_user.id
    ).count()
    
    # Bekleyen ödemeler
    pending_payments = db.query(PaymentRequest).filter(
        PaymentRequest.merchant_id == current_user.id,
        PaymentRequest.status == PaymentStatus.PENDING
    ).count()
    
    # Onaylanmış ödemeler
    confirmed_payments = db.query(PaymentRequest).filter(
        PaymentRequest.merchant_id == current_user.id,
        PaymentRequest.status == PaymentStatus.CONFIRMED
    ).count()
    
    # Toplam miktar
    total_amount_result = db.query(
        db.func.sum(PaymentRequest.amount)
    ).filter(
        PaymentRequest.merchant_id == current_user.id,
        PaymentRequest.status == PaymentStatus.CONFIRMED
    ).scalar()
    
    total_amount = Decimal(str(total_amount_result or 0))
    
    # Bugünkü ödemeler
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_payments = db.query(PaymentRequest).filter(
        PaymentRequest.merchant_id == current_user.id,
        PaymentRequest.created_at >= today_start
    ).count()
    
    # Bugünkü miktar
    today_amount_result = db.query(
        db.func.sum(PaymentRequest.amount)
    ).filter(
        PaymentRequest.merchant_id == current_user.id,
        PaymentRequest.status == PaymentStatus.CONFIRMED,
        PaymentRequest.confirmed_at >= today_start
    ).scalar()
    
    today_amount = Decimal(str(today_amount_result or 0))
    
    return DashboardStats(
        total_payments=total_payments,
        pending_payments=pending_payments,
        confirmed_payments=confirmed_payments,
        total_amount=total_amount,
        today_payments=today_payments,
        today_amount=today_amount
    )

@router.get("/islemler/{payment_id}", response_model=List[TransactionResponse], summary="Ödeme işlemleri")
async def get_payment_transactions(
    payment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Belirli bir ödemeye ait blockchain işlemlerini listele
    """
    # Ödemenin kullanıcıya ait olduğunu kontrol et
    payment = db.query(PaymentRequest).filter(
        PaymentRequest.id == payment_id,
        PaymentRequest.merchant_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ödeme bulunamadı"
        )
    
    # İşlemleri al
    transactions = db.query(Transaction).filter(
        Transaction.payment_request_id == payment_id
    ).order_by(Transaction.detected_at.desc()).all()
    
    return transactions

@router.post("/iptal/{payment_id}", summary="Ödeme iptal et")
async def cancel_payment(
    payment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Bekleyen ödemeyi iptal et
    """
    payment = db.query(PaymentRequest).filter(
        PaymentRequest.id == payment_id,
        PaymentRequest.merchant_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ödeme bulunamadı"
        )
    
    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece bekleyen ödemeler iptal edilebilir"
        )
    
    # Ödemeyi iptal et
    payment.status = PaymentStatus.FAILED
    db.commit()
    
    return {"message": "Ödeme iptal edildi"}

@router.get("/qr/{payment_id}", summary="QR kod al")
async def get_payment_qr(
    payment_id: int,
    current_user: User = Depends(get_api_user),
    db: Session = Depends(get_db)
):
    """
    Ödeme için QR kod oluştur
    """
    payment = db.query(PaymentRequest).filter(
        PaymentRequest.id == payment_id,
        PaymentRequest.merchant_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ödeme bulunamadı"
        )
    
    # QR kod oluştur
    qr_code_data = CryptoService.generate_payment_qr(
        payment.payment_address,
        float(payment.amount),
        payment.currency
    )
    
    return {
        "qr_code": qr_code_data,
        "payment_address": payment.payment_address,
        "amount": payment.amount,
        "currency": payment.currency
    } 