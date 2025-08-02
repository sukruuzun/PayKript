import httpx
import json
import asyncio
from typing import Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_webhook_signature
from app.db.models import PaymentRequest, Transaction
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)

class WebhookService:
    """
    Webhook bildirim servisi
    Ödeme onaylandığında merchant'a bildirim gönderir
    """
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delays = [1, 5, 15]  # Saniye cinsinden bekleme süreleri
    
    async def send_payment_confirmation(self, payment: PaymentRequest, transaction: Transaction):
        """
        Ödeme onay webhook'u gönder
        """
        if not payment.webhook_url:
            logger.warning(f"Webhook URL tanımlanmamış: {payment.order_id}")
            return
        
        # Webhook payload'ı hazırla
        payload = self._prepare_payment_payload(payment, transaction)
        
        # Webhook gönder (retry ile)
        success = await self._send_webhook_with_retry(
            payment.webhook_url,
            payload,
            payment.id
        )
        
        # Database'i güncelle
        await self._update_webhook_status(payment.id, success)
    
    def _prepare_payment_payload(self, payment: PaymentRequest, transaction: Transaction) -> dict:
        """
        Webhook payload'ını hazırla
        """
        return {
            "event": "payment.confirmed",
            "data": {
                "payment_id": payment.id,
                "order_id": payment.order_id,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "status": payment.status.value,
                "payment_address": payment.payment_address,
                "confirmed_at": payment.confirmed_at.isoformat() if payment.confirmed_at else None,
                "transaction": {
                    "tx_hash": transaction.tx_hash,
                    "from_address": transaction.from_address,
                    "amount": str(transaction.amount),
                    "confirmations": transaction.confirmations,
                    "block_number": transaction.block_number,
                    "network": transaction.network
                },
                "customer_email": payment.customer_email,
                "notes": payment.notes
            },
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0"
        }
    
    async def _send_webhook_with_retry(self, webhook_url: str, payload: dict, payment_id: int) -> bool:
        """
        Webhook'u retry mekanizması ile gönder
        """
        payload_json = json.dumps(payload, sort_keys=True)
        
        # HMAC imzası oluştur
        signature = create_webhook_signature(payload_json, settings.WEBHOOK_SECRET)
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "PayKript-Webhook/1.0",
            "X-PayKript-Signature": signature,
            "X-PayKript-Event": payload["event"],
            "X-PayKript-Timestamp": payload["timestamp"]
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Webhook gönderiliyor (deneme {attempt + 1}): {webhook_url}")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        webhook_url,
                        content=payload_json,
                        headers=headers
                    )
                    
                    # 2xx response kodları başarılı sayılır
                    if 200 <= response.status_code < 300:
                        logger.info(f"Webhook başarılı: {webhook_url} - {response.status_code}")
                        return True
                    else:
                        logger.warning(f"Webhook başarısız: {webhook_url} - {response.status_code}")
                        
            except Exception as e:
                logger.error(f"Webhook hatası (deneme {attempt + 1}): {webhook_url} - {e}")
            
            # Son deneme değilse bekle
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delays[attempt])
        
        logger.error(f"Webhook tüm denemeler başarısız: {webhook_url}")
        return False
    
    async def _update_webhook_status(self, payment_id: int, success: bool):
        """
        Webhook durumunu database'de güncelle
        """
        try:
            db = SessionLocal()
            
            payment = db.query(PaymentRequest).filter(
                PaymentRequest.id == payment_id
            ).first()
            
            if payment:
                payment.webhook_sent = success
                payment.webhook_attempts += 1
                db.commit()
                
            db.close()
            
        except Exception as e:
            logger.error(f"Webhook durumu güncelleme hatası: {e}")
    
    async def test_webhook_endpoint(self, webhook_url: str) -> dict:
        """
        Webhook endpoint'ini test et
        """
        test_payload = {
            "event": "webhook.test",
            "data": {
                "message": "Bu bir test webhook'udur",
                "timestamp": datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0"
        }
        
        try:
            payload_json = json.dumps(test_payload, sort_keys=True)
            signature = create_webhook_signature(payload_json, settings.WEBHOOK_SECRET)
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "PayKript-Webhook/1.0",
                "X-PayKript-Signature": signature,
                "X-PayKript-Event": test_payload["event"],
                "X-PayKript-Timestamp": test_payload["timestamp"]
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    webhook_url,
                    content=payload_json,
                    headers=headers
                )
                
                return {
                    "success": 200 <= response.status_code < 300,
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "response_body": response.text[:500]  # İlk 500 karakter
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": None,
                "response_time_ms": None
            }
    
    async def resend_webhook(self, payment_id: int) -> bool:
        """
        Başarısız webhook'u yeniden gönder
        """
        try:
            db = SessionLocal()
            
            payment = db.query(PaymentRequest).filter(
                PaymentRequest.id == payment_id
            ).first()
            
            if not payment:
                logger.error(f"Ödeme bulunamadı: {payment_id}")
                return False
            
            if not payment.webhook_url:
                logger.error(f"Webhook URL tanımlanmamış: {payment_id}")
                return False
            
            # İlişkili transaction'ı bul
            transaction = payment.transactions[0] if payment.transactions else None
            if not transaction:
                logger.error(f"Transaction bulunamadı: {payment_id}")
                return False
            
            db.close()
            
            # Webhook gönder
            await self.send_payment_confirmation(payment, transaction)
            return True
            
        except Exception as e:
            logger.error(f"Webhook yeniden gönderme hatası: {e}")
            return False

# Singleton instance
webhook_service = WebhookService() 