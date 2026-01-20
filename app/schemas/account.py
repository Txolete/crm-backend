"""
Pydantic schemas for Account
"""
from pydantic import BaseModel, Field
from typing import Optional


class AccountBase(BaseModel):
    """Base account schema"""
    name: str = Field(..., min_length=1, max_length=200)
    
    # Contact info
    website: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    
    # Legal/fiscal
    tax_id: Optional[str] = Field(None, max_length=50)
    
    # Classification
    region_id: Optional[str] = None
    region_other_text: Optional[str] = None
    customer_type_id: Optional[str] = None
    customer_type_other_text: Optional[str] = None
    lead_source_id: Optional[str] = None
    lead_source_detail: Optional[str] = None
    
    # Management
    owner_user_id: Optional[str] = None
    
    # Notes
    notes: Optional[str] = None


class AccountCreate(AccountBase):
    """Schema for creating an account"""
    pass


class AccountUpdate(BaseModel):
    """Schema for updating an account"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    
    # Contact info
    website: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    
    # Legal/fiscal
    tax_id: Optional[str] = Field(None, max_length=50)
    
    # Classification
    region_id: Optional[str] = None
    region_other_text: Optional[str] = None
    customer_type_id: Optional[str] = None
    customer_type_other_text: Optional[str] = None
    lead_source_id: Optional[str] = None
    lead_source_detail: Optional[str] = None
    
    # Management
    owner_user_id: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|archived)$")
    
    # Notes
    notes: Optional[str] = None


class AccountResponse(BaseModel):
    """Schema for account response"""
    id: str
    name: str
    
    # Contact info
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    
    # Legal/fiscal
    tax_id: Optional[str] = None
    
    # Classification
    region_id: Optional[str] = None
    region_other_text: Optional[str] = None
    customer_type_id: Optional[str] = None
    customer_type_other_text: Optional[str] = None
    lead_source_id: Optional[str] = None
    lead_source_detail: Optional[str] = None
    
    # Management
    owner_user_id: Optional[str] = None
    status: str
    
    # Notes
    notes: Optional[str] = None
    
    # Counters (computed)
    opportunities_count: int = 0
    contacts_count: int = 0
    
    # Audit
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AccountListResponse(BaseModel):
    """Schema for list of accounts"""
    accounts: list[AccountResponse]
    total: int


class AccountDetailResponse(AccountResponse):
    """
    Schema for detailed account response
    Includes contacts, opportunities count, and other stats
    """
    # Stats
    opportunities_count: int = 0
    contacts_count: int = 0
    pipeline_total: float = 0.0
    
    # Will be populated by endpoint
    contacts: list = []
    opportunities: list = []

