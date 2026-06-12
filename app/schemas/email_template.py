from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from datetime import datetime


class EmailTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=50)
    subject: str = Field(..., min_length=1, max_length=300)
    body: str = Field(..., min_length=1)
    required_variables: str = Field("senal_detectada", max_length=300)
    notes: Optional[str] = None
    is_active: Optional[bool] = True


class EmailTemplateCreate(EmailTemplateBase):
    pass


class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    required_variables: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class EmailTemplateResponse(BaseModel):
    id: str
    name: str
    category: Optional[str]
    subject: str
    body: str
    required_variables: str
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    sent_count: int = 0
    response_count: int = 0

    class Config:
        from_attributes = True


class EmailTemplateListResponse(BaseModel):
    templates: List[EmailTemplateResponse]
    total: int


class RenderRequest(BaseModel):
    variables: Dict[str, str] = Field(default_factory=dict)


class RenderResponse(BaseModel):
    subject: str
    body: str
    missing_required: List[str] = []


class EmailSentCreate(BaseModel):
    template_id: Optional[str] = None
    account_id: Optional[str] = None
    contact_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    to_email: str
    to_name: Optional[str] = None
    subject: str
    body: str
    senal_detectada: Optional[str] = None


class EmailSentResponse(BaseModel):
    id: str
    template_id: Optional[str]
    template_name_snapshot: Optional[str]
    account_id: Optional[str]
    contact_id: Optional[str]
    opportunity_id: Optional[str]
    to_email: str
    to_name: Optional[str]
    subject: str
    body: str
    senal_detectada: Optional[str]
    sent_at: datetime
    sent_by_user_id: Optional[str]
    sent_by_name: Optional[str] = None
    response_received: bool
    response_at: Optional[datetime]
    response_note: Optional[str]

    class Config:
        from_attributes = True


class EmailSentListResponse(BaseModel):
    emails: List[EmailSentResponse]
    total: int


class MarkResponseRequest(BaseModel):
    response_note: Optional[str] = None
    response_received: bool = True
