from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.db.database import engine
from app.db import models

# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PayKript API",
    description="Kripto Ödeme Doğrulama Platformu API",
    version="1.0.0",
    docs_url=f"{settings.API_V1_STR}/docs",        # Swagger UI
    redoc_url=f"{settings.API_V1_STR}/redoc",      # ReDoc
    openapi_url=f"{settings.API_V1_STR}/openapi.json"  # OpenAPI spec
)

# CORS Middleware
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Trusted Host Middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# API Router'ları ekle
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": "PayKript API'ye hoş geldiniz",
        "version": "1.0.0",
        "docs": f"{settings.API_V1_STR}/docs" if settings.ENVIRONMENT == "development" else None
    }

@app.get("/health")
async def health_check():
    return {"status": "OK", "service": "PayKript API"}

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000))  # Railway $PORT kullan, fallback 8000
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    ) 