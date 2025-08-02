from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from app.db.models import UserRole

# Base User schema
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None

# User creation schema
class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Şifre en az 8 karakter olmalıdır')
        return v

# User update schema
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

# User response schema
class User(UserBase):
    id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}

# Login schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    email: Optional[str] = None 