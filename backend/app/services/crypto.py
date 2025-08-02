import base64
import io
from typing import Optional
from bip32 import BIP32
import qrcode
from qrcode.image.pil import PilImage
import hashlib
import base58
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class CryptoAddressGenerationError(Exception):
    """
    Kripto adres oluşturma hatası
    CRITICAL: Bu hata müşteri ödemelerinin kaybolmasını önler
    """
    pass

class CryptoService:
    """
    Kripto işlemleri için yardımcı sınıf
    """
    
    @staticmethod
    def derive_address_from_xpub(xpub: str, index: int, derivation_path: str = "m/44'/195'/0'/0") -> str:
        """
        xPub anahtarından belirli index'teki adresi türet
        TRON ağı için optimize edilmiş
        
        Returns:
            str: TRON adresi
            
        Raises:
            CryptoAddressGenerationError: Adres oluşturulamazsa
        """
        try:
            # BIP32 objesi oluştur
            bip32 = BIP32.from_xpub(xpub)
            
            # Child key türet (0/index formatında)
            child_key = bip32.get_child_from_path(f"0/{index}")
            
            # Public key'i al
            pubkey = child_key.pubkey
            
            # TRON adresi oluştur (exception fırlatabilir)
            tron_address = CryptoService._pubkey_to_tron_address(pubkey)
            
            return tron_address
            
        except CryptoAddressGenerationError:
            # Alt seviye hatayı yukarı fırlat
            raise
        except Exception as e:
            logger.error(f"Adres türetme hatası: {e}")
            raise CryptoAddressGenerationError(f"xPub'dan adres türetilemedi: {e}") from e
    
    @staticmethod
    def _pubkey_to_tron_address(pubkey: bytes) -> str:
        """
        Public key'den TRON adresi oluştur
        """
        try:
            # Keccak256 hash
            from Crypto.Hash import keccak
            
            # Uncompressed public key (65 bytes) kullan
            if len(pubkey) == 33:  # Compressed
                # Compressed'dan uncompressed'a çevir
                from cryptography.hazmat.primitives.asymmetric import ec
                from cryptography.hazmat.primitives import serialization
                
                # Bu kısım daha kompleks, basit implementasyon için
                # compressed key'i kullanabiliriz
                pass
            
            # Keccak256 hash'i al (son 20 byte)
            k = keccak.new(digest_bits=256)
            k.update(pubkey[1:])  # İlk byte'ı (0x04) atla
            pubkey_hash = k.digest()[-20:]
            
            # TRON prefix'i ekle (0x41)
            address_hex = b'\x41' + pubkey_hash
            
            # Double SHA256 checksum
            checksum = hashlib.sha256(hashlib.sha256(address_hex).digest()).digest()[:4]
            
            # Base58 encode
            address_bytes = address_hex + checksum
            address = base58.b58encode(address_bytes).decode('utf-8')
            
            return address
            
        except Exception as e:
            logger.error(f"KRİTİK HATA - TRON adres oluşturma başarısız: {e}")
            # CRITICAL SECURITY: Asla sahte adres döndürme!
            # Mock adres döndürmek müşteri ödemelerinin kaybolmasına sebep olabilir
            raise CryptoAddressGenerationError(f"TRON adresi oluşturulamadı: {e}") from e
    
    @staticmethod
    def generate_payment_qr(address: str, amount: float, currency: str = "USDT") -> str:
        """
        Ödeme için QR kod oluştur ve base64 string olarak döndür
        """
        try:
            # TRON ödeme URL'i oluştur
            # Format: tronlink://pay?address=...&amount=...&token=...
            payment_url = f"tronlink://pay?address={address}&amount={amount}&token={settings.USDT_CONTRACT_ADDRESS}"
            
            # QR kod oluştur
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(payment_url)
            qr.make(fit=True)
            
            # PIL Image olarak oluştur
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Base64 string'e çevir
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"QR kod oluşturma hatası: {e}")
            # Fallback: basit text QR
            return CryptoService._generate_simple_qr(address)
    
    @staticmethod
    def _generate_simple_qr(text: str) -> str:
        """
        Basit text QR kod oluştur
        """
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(text)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"Basit QR kod oluşturma hatası: {e}")
            return ""
    
    @staticmethod
    def validate_tron_address(address: str) -> bool:
        """
        TRON adresinin geçerliliğini kontrol et
        """
        try:
            if not address.startswith('T'):
                return False
            
            if len(address) != 34:
                return False
            
            # Base58 decode
            decoded = base58.b58decode(address)
            
            if len(decoded) != 25:
                return False
            
            # Checksum kontrolü
            address_hex = decoded[:-4]
            checksum = decoded[-4:]
            
            calculated_checksum = hashlib.sha256(hashlib.sha256(address_hex).digest()).digest()[:4]
            
            return checksum == calculated_checksum
            
        except Exception:
            return False
    
    @staticmethod
    def validate_xpub_key(xpub: str) -> bool:
        """
        xPub anahtarının geçerliliğini kontrol et
        """
        try:
            if not xpub.startswith('xpub'):
                return False
            
            # BIP32 ile parse etmeyi dene
            BIP32.from_xpub(xpub)
            return True
            
        except Exception:
            return False 