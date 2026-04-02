"""
Pydantic schemas for User
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    name: str


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(admin|sales|commercial|viewer)$")


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern="^(admin|sales|commercial|viewer)$")
    is_active: Optional[bool] = None


class UserResetPassword(BaseModel):
    """Schema for resetting password"""
    new_password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    """Schema for user response (NEVER includes password_hash)"""
    id: str
    name: str
    email: str
    role: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for list of users"""
    users: list[UserResponse]
    total: int
