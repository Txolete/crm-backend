"""
Pydantic schemas for Activity
"""
from pydantic import BaseModel, Field
from typing import Optional


class ActivityCreate(BaseModel):
    """Schema for creating an activity"""
    opportunity_id: str
    type: str = Field(..., pattern="^(status_change|task_created|task_completed|note|call|meeting|email|won|lost)$")
    summary: str = Field(..., min_length=1, max_length=500)
    occurred_at: Optional[str] = None  # ISO datetime, defaults to now if not provided


class ActivityUpdate(BaseModel):
    """Schema for updating an activity"""
    summary: Optional[str] = Field(None, min_length=1, max_length=500)
    occurred_at: Optional[str] = None


class ActivityResponse(BaseModel):
    """Schema for activity response"""
    id: str
    opportunity_id: str
    type: str
    occurred_at: str
    summary: str
    created_by_user_id: Optional[str] = None
    created_by_name: Optional[str] = None  # Computed field
    created_at: str

    class Config:
        from_attributes = True


class ActivityListResponse(BaseModel):
    """Schema for list of activities"""
    activities: list[ActivityResponse]
    total: int

