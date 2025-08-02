from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.db.models import PaymentStatus, TransactionStatus

# Payment Request schemas
class PaymentRequestCreate(BaseModel):
    order_id: str
    amount: Decimal
    currency: str = "USDT"
    webhook_url: Optional[str] = None
    customer_email: Optional[str] = None
    customer_info: Optional[str] = None
    notes: Optional[str] = None
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Ödeme miktarı 0\'dan büyük olmalıdır')
        if v > 1000000:  # 1M USDT limit
            raise ValueError('Maksimum ödeme miktarı 1.000.000 USDT\'dir')
        return v
    
    @field_validator('order_id')
    @classmethod
    def validate_order_id(cls, v):
        if len(v) < 1 or len(v) > 255:
            raise ValueError('Sipariş ID\'si 1-255 karakter arasında olmalıdır')
        return v

class PaymentRequestResponse(BaseModel):
    id: int
    order_id: str
    amount: Decimal
    currency: str
    payment_address: str
    status: PaymentStatus
    expires_at: datetime
    created_at: datetime
    qr_code_data: str  # Base64 encoded QR code or QR data string
    
    model_config = {"from_attributes": True}

class PaymentRequestDetail(PaymentRequestResponse):
    merchant_id: int
    wallet_id: int
    address_index: int
    confirmed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    webhook_url: Optional[str] = None
    webhook_sent: bool
    webhook_attempts: int
    customer_email: Optional[str] = None
    customer_info: Optional[str] = None
    notes: Optional[str] = None

# Transaction schemas
class TransactionBase(BaseModel):
    tx_hash: str
    from_address: str
    to_address: str
    amount: Decimal
    network: str = "tron"
    contract_address: Optional[str] = None

class TransactionResponse(TransactionBase):
    id: int
    payment_request_id: int
    block_number: Optional[int] = None
    block_timestamp: Optional[datetime] = None
    confirmations: int
    status: TransactionStatus
    detected_at: datetime
    confirmed_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

# Wallet schemas
class WalletCreate(BaseModel):
    wallet_name: str
    xpub_key: str
    network: str = "tron"
    derivation_path: str = "m/44'/195'/0'/0"
    
    @field_validator('wallet_name')
    @classmethod
    def validate_wallet_name(cls, v):
        if len(v) < 1 or len(v) > 255:
            raise ValueError('Cüzdan adı 1-255 karakter arasında olmalıdır')
        return v
    
    @field_validator('xpub_key')
    @classmethod
    def validate_xpub_key(cls, v):
        if not v.startswith('xpub'):
            raise ValueError('Geçerli bir xPub anahtarı giriniz')
        return v

class WalletResponse(BaseModel):
    id: int
    wallet_name: str
    network: str
    derivation_path: str
    address_index: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

# API Key schemas
class APIKeyCreate(BaseModel):
    key_name: str
    
    @field_validator('key_name')
    @classmethod
    def validate_key_name(cls, v):
        if len(v) < 1 or len(v) > 255:
            raise ValueError('API anahtarı adı 1-255 karakter arasında olmalıdır')
        return v

class APIKeyResponse(BaseModel):
    id: int
    key_name: str
    api_key: str
    secret_key: str  # Sadece oluşturulurken gösterilir
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}

class APIKeyList(BaseModel):
    id: int
    key_name: str
    api_key: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}

# Payment status update (for webhooks)
class PaymentStatusUpdate(BaseModel):
    payment_id: int
    status: PaymentStatus
    tx_hash: Optional[str] = None
    confirmed_at: Optional[datetime] = None

# Dashboard statistics
class DashboardStats(BaseModel):
    total_payments: int
    pending_payments: int
    confirmed_payments: int
    total_amount: Decimal
    today_payments: int
    today_amount: Decimal 