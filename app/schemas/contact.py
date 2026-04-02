"""
Pydantic schemas for Contact and ContactChannel
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class ContactChannelBase(BaseModel):
    """Base contact channel schema"""
    type: str = Field(..., pattern="^(email|phone)$")
    value: str = Field(..., min_length=1)
    is_primary: bool = False


class ContactChannelCreate(ContactChannelBase):
    """Schema for creating a contact channel"""
    pass


class ContactChannelUpdate(BaseModel):
    """Schema for updating a contact channel"""
    value: Optional[str] = Field(None, min_length=1)
    is_primary: Optional[bool] = None


class ContactChannelResponse(BaseModel):
    """Schema for contact channel response"""
    id: str
    contact_id: str
    type: str
    value: str
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ContactBase(BaseModel):
    """Base contact schema"""
    account_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    contact_role_id: Optional[str] = None
    contact_role_other_text: Optional[str] = None


class ContactCreate(ContactBase):
    """Schema for creating a contact"""
    channels: Optional[List[ContactChannelCreate]] = []


class ContactUpdate(BaseModel):
    """Schema for updating a contact"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    contact_role_id: Optional[str] = None
    contact_role_other_text: Optional[str] = None
    channels: Optional[List[ContactChannelCreate]] = None


class ContactResponse(BaseModel):
    """Schema for contact response"""
    id: str
    account_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    contact_role_id: Optional[str] = None
    contact_role_other_text: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    channels: List[ContactChannelResponse] = []

    class Config:
        from_attributes = True


class ContactListResponse(BaseModel):
    """Schema for list of contacts"""
    contacts: list[ContactResponse]
    total: int
