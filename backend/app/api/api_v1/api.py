from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, payments, wallets

api_router = APIRouter()

# Auth endpoints
api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["Kimlik Doğrulama"]
)

# Payment endpoints
api_router.include_router(
    payments.router, 
    prefix="/odemeler", 
    tags=["Ödemeler"]
)

# Wallet & API Key endpoints
api_router.include_router(
    wallets.router, 
    prefix="/yonetim", 
    tags=["Cüzdan ve API Yönetimi"]
) 