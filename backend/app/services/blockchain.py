import httpx
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import PaymentRequest, Transaction, PaymentStatus, TransactionStatus
from app.services.webhook import WebhookService

logger = logging.getLogger(__name__)

class BlockchainMonitor:
    """
    Blockchain izleme servisi
    TronGrid API kullanarak USDT ödemelerini izler
    """
    
    def __init__(self):
        self.trongrid_url = settings.TRON_GRID_BASE_URL
        self.api_key = settings.TRON_GRID_API_KEY
        self.usdt_contract = settings.USDT_CONTRACT_ADDRESS
        self.webhook_service = WebhookService()
        
    async def monitor_pending_payments(self):
        """
        Bekleyen ödemeleri sürekli izle
        """
        logger.info("Blockchain monitoring başlatılıyor...")
        
        while True:
            try:
                db = SessionLocal()
                
                # Bekleyen ödemeleri al
                pending_payments = db.query(PaymentRequest).filter(
                    PaymentRequest.status == PaymentStatus.PENDING,
                    PaymentRequest.expires_at > datetime.utcnow()
                ).all()
                
                logger.info(f"{len(pending_payments)} bekleyen ödeme kontrol ediliyor...")
                
                # Her ödemeyi kontrol et
                tasks = []
                for payment in pending_payments:
                    task = self.check_payment_address(payment, db)
                    tasks.append(task)
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Süresi dolmuş ödemeleri işaretle
                await self.mark_expired_payments(db)
                
                db.close()
                
                # 30 saniye bekle
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Monitoring döngüsü hatası: {e}")
                await asyncio.sleep(60)  # Hata durumunda daha uzun bekle
    
    async def check_payment_address(self, payment: PaymentRequest, db: Session):
        """
        Belirli bir ödeme adresini kontrol et
        """
        try:
            # TronGrid API'den işlemleri al
            transactions = await self.get_address_transactions(payment.payment_address)
            
            for tx in transactions:
                # USDT transferi mi kontrol et
                if await self.is_usdt_transfer(tx, payment.payment_address, payment.amount):
                    # Bu işlem zaten kayıtlı mı?
                    existing_tx = db.query(Transaction).filter(
                        Transaction.tx_hash == tx['transaction_id']
                    ).first()
                    
                    if not existing_tx:
                        # Yeni işlem kaydet
                        new_tx = Transaction(
                            payment_request_id=payment.id,
                            tx_hash=tx['transaction_id'],
                            from_address=tx.get('from_address', ''),
                            to_address=payment.payment_address,
                            amount=Decimal(str(tx.get('amount', 0))) / 1000000,  # USDT 6 decimal
                            network="tron",
                            contract_address=self.usdt_contract,
                            block_number=tx.get('block_number'),
                            block_timestamp=datetime.fromtimestamp(tx.get('timestamp', 0) / 1000),
                            confirmations=tx.get('confirmations', 0),
                            status=TransactionStatus.CONFIRMED if tx.get('confirmations', 0) >= settings.REQUIRED_CONFIRMATIONS else TransactionStatus.PENDING
                        )
                        
                        db.add(new_tx)
                        
                        # Yeterli onayı varsa ödemeyi onayla
                        if tx.get('confirmations', 0) >= settings.REQUIRED_CONFIRMATIONS:
                            await self.confirm_payment(payment, new_tx, db)
                    
                    else:
                        # Mevcut işlemi güncelle
                        existing_tx.confirmations = tx.get('confirmations', 0)
                        existing_tx.block_number = tx.get('block_number')
                        
                        # Yeterli onayı varsa ve henüz onaylanmamışsa
                        if (tx.get('confirmations', 0) >= settings.REQUIRED_CONFIRMATIONS and 
                            payment.status == PaymentStatus.PENDING):
                            await self.confirm_payment(payment, existing_tx, db)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Adres kontrolü hatası {payment.payment_address}: {e}")
            db.rollback()
    
    async def get_address_transactions(self, address: str) -> List[Dict]:
        """
        TronGrid API'den adres işlemlerini al
        """
        try:
            headers = {"TRON-PRO-API-KEY": self.api_key} if self.api_key else {}
            
            # TRC20 transferlerini al
            url = f"{self.trongrid_url}/v1/accounts/{address}/transactions/trc20"
            params = {
                "limit": 50,
                "contract_address": self.usdt_contract
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                return data.get('data', [])
                
        except Exception as e:
            logger.error(f"TronGrid API hatası: {e}")
            return []
    
    async def is_usdt_transfer(self, tx: Dict, to_address: str, expected_amount: Decimal) -> bool:
        """
        İşlemin beklenen USDT transferi olup olmadığını kontrol et
        """
        try:
            # Alıcı adres kontrolü
            if tx.get('to') != to_address:
                return False
            
            # Token contract kontrolü
            if tx.get('token_info', {}).get('address') != self.usdt_contract:
                return False
            
            # Miktar kontrolü (6 decimal USDT)
            tx_amount = Decimal(str(tx.get('value', 0))) / 1000000
            
            # Miktar eşleşmesi (küçük farkları tolere et)
            amount_diff = abs(tx_amount - expected_amount)
            if amount_diff > Decimal('0.01'):  # 0.01 USDT tolerans
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"USDT transfer kontrolü hatası: {e}")
            return False
    
    async def confirm_payment(self, payment: PaymentRequest, transaction: Transaction, db: Session):
        """
        Ödemeyi onayla ve webhook gönder
        """
        try:
            # Ödeme durumunu güncelle
            payment.status = PaymentStatus.CONFIRMED
            payment.confirmed_at = datetime.utcnow()
            
            # Transaction durumunu güncelle
            transaction.status = TransactionStatus.CONFIRMED
            transaction.confirmed_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Ödeme onaylandı: {payment.order_id} - {payment.amount} USDT")
            
            # Webhook gönder
            if payment.webhook_url:
                await self.webhook_service.send_payment_confirmation(payment, transaction)
            
        except Exception as e:
            logger.error(f"Ödeme onaylama hatası: {e}")
            db.rollback()
    
    async def mark_expired_payments(self, db: Session):
        """
        Süresi dolmuş ödemeleri işaretle
        """
        try:
            expired_payments = db.query(PaymentRequest).filter(
                PaymentRequest.status == PaymentStatus.PENDING,
                PaymentRequest.expires_at <= datetime.utcnow()
            ).all()
            
            for payment in expired_payments:
                payment.status = PaymentStatus.EXPIRED
                logger.info(f"Ödeme süresi doldu: {payment.order_id}")
            
            if expired_payments:
                db.commit()
                logger.info(f"{len(expired_payments)} ödemenin süresi doldu")
                
        except Exception as e:
            logger.error(f"Süresi dolmuş ödeme işaretleme hatası: {e}")
            db.rollback()
    
    async def get_transaction_details(self, tx_hash: str) -> Optional[Dict]:
        """
        İşlem detaylarını TronGrid'den al
        """
        try:
            headers = {"TRON-PRO-API-KEY": self.api_key} if self.api_key else {}
            url = f"{self.trongrid_url}/wallet/gettransactionbyid"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url, 
                    headers=headers,
                    json={"value": tx_hash}
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"İşlem detayları alma hatası: {e}")
            return None

# Singleton instance
blockchain_monitor = BlockchainMonitor() 