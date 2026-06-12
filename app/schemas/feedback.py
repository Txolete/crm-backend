from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FeedbackCreate(BaseModel):
    message: str = Field(..., min_length=3, max_length=5000)
    view: Optional[str] = Field(None, max_length=80)
    url: Optional[str] = Field(None, max_length=500)


class FeedbackResponse(BaseModel):
    id: str
    user_id: Optional[str]
    user_name: Optional[str] = None
    message: str
    view: Optional[str]
    url: Optional[str]
    user_agent: Optional[str]
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by_user_id: Optional[str] = None
    admin_note: Optional[str] = None

    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    feedback: List[FeedbackResponse]
    total: int


class FeedbackUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(open|reviewed|done|discarded)$")
    admin_note: Optional[str] = Field(None, max_length=2000)
