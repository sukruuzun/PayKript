from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum
from datetime import datetime
from typing import Optional

class UserRole(str, enum.Enum):
    MERCHANT = "merchant"
    ADMIN = "admin"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"           # Ödeme bekleniyor
    CONFIRMED = "confirmed"       # Ödeme onaylandı
    EXPIRED = "expired"          # Ödeme süresi doldu
    FAILED = "failed"            # Ödeme başarısız

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"

# Satıcı (Merchant) kullanıcıları
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.MERCHANT)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # İlişkiler
    wallets = relationship("MerchantWallet", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    payment_requests = relationship("PaymentRequest", back_populates="merchant")

# Satıcı cüzdanları (xPub anahtarları)
class MerchantWallet(Base):
    __tablename__ = "merchant_wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wallet_name = Column(String(255), nullable=False)  # Kullanıcının verdiği isim
    xpub_key = Column(Text, nullable=False)  # Extended Public Key
    network = Column(String(50), default="tron")  # tron, ethereum vs.
    derivation_path = Column(String(100), default="m/44'/195'/0'/0")  # TRON derivation path
    address_index = Column(Integer, default=0)  # Son kullanılan adres indexi
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # İlişkiler
    user = relationship("User", back_populates="wallets")
    payment_requests = relationship("PaymentRequest", back_populates="wallet")

# API Anahtarları
class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_name = Column(String(255), nullable=False)  # Kullanıcının verdiği isim
    api_key = Column(String(255), unique=True, index=True, nullable=False)
    secret_key = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # İlişkiler
    user = relationship("User", back_populates="api_keys")

# Ödeme talepleri
class PaymentRequest(Base):
    __tablename__ = "payment_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wallet_id = Column(Integer, ForeignKey("merchant_wallets.id"), nullable=False)
    
    # Ödeme bilgileri
    order_id = Column(String(255), nullable=False)  # Satıcının sipariş ID'si
    amount = Column(Numeric(precision=18, scale=6), nullable=False)  # USDT miktarı
    currency = Column(String(10), default="USDT")
    
    # Adres bilgileri
    payment_address = Column(String(255), nullable=False)  # Üretilen benzersiz adres
    address_index = Column(Integer, nullable=False)  # Bu adresin wallet'taki index'i
    
    # Durum ve zaman bilgileri
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Webhook bilgileri
    webhook_url = Column(String(500), nullable=True)  # Ödeme onaylandığında bildirim gönderilecek URL
    webhook_sent = Column(Boolean, default=False)
    webhook_attempts = Column(Integer, default=0)
    
    # Metadata
    customer_email = Column(String(255), nullable=True)
    customer_info = Column(Text, nullable=True)  # JSON format
    notes = Column(Text, nullable=True)
    
    # İlişkiler
    merchant = relationship("User", back_populates="payment_requests")
    wallet = relationship("MerchantWallet", back_populates="payment_requests")
    transactions = relationship("Transaction", back_populates="payment_request")

# Blockchain işlemleri
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_request_id = Column(Integer, ForeignKey("payment_requests.id"), nullable=False)
    
    # Blockchain bilgileri
    tx_hash = Column(String(255), unique=True, index=True, nullable=False)
    from_address = Column(String(255), nullable=False)
    to_address = Column(String(255), nullable=False)
    amount = Column(Numeric(precision=18, scale=6), nullable=False)
    
    # Network bilgileri
    network = Column(String(50), default="tron")
    contract_address = Column(String(255), nullable=True)  # Token contract adresi
    block_number = Column(Integer, nullable=True)
    block_timestamp = Column(DateTime(timezone=True), nullable=True)
    confirmations = Column(Integer, default=0)
    
    # Durum
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    
    # Zaman bilgileri
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    
    # İlişkiler
    payment_request = relationship("PaymentRequest", back_populates="transactions") 