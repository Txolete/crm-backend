"""
Pydantic schemas for Authentication
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime


class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Schema for login response"""
    message: str
    user: dict | None = None  # Will contain: id, name, email, role
    requires_2fa: bool = False
    challenge_id: str | None = None


class Verify2FARequest(BaseModel):
    """Schema for 2FA code verification"""
    challenge_id: str
    code: str


class Resend2FARequest(BaseModel):
    """Schema to resend a 2FA code"""
    challenge_id: str


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
    last_login_at: datetime | None = None
    email_signature: str | None = None
