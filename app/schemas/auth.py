"""
Pydantic schemas for Authentication
"""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Schema for login response"""
    message: str
    user: dict  # Will contain: id, name, email, role


class LogoutResponse(BaseModel):
    """Schema for logout response"""
    message: str


class MeResponse(BaseModel):
    """Schema for /auth/me response"""
    id: str
    name: str
    email: str
    role: str
    is_active: bool
    last_login_at: str | None = None
