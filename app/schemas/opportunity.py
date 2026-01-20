"""
Pydantic schemas for Opportunity
"""
from pydantic import BaseModel, Field
from typing import Optional


class OpportunityBase(BaseModel):
    """Base opportunity schema"""
    account_id: str
    name: Optional[str] = None
    stage_id: str
    stage_detail: Optional[str] = None
    expected_value_eur: float = Field(..., ge=0)
    weighted_value_override_eur: Optional[float] = Field(None, ge=0)
    probability_override: Optional[float] = Field(None, ge=0, le=1)
    forecast_close_month: Optional[str] = None
    owner_user_id: Optional[str] = None


class OpportunityCreate(OpportunityBase):
    """Schema for creating an opportunity"""
    pass


class OpportunityUpdate(BaseModel):
    """Schema for updating an opportunity"""
    name: Optional[str] = None
    stage_id: Optional[str] = None
    stage_detail: Optional[str] = None
    expected_value_eur: Optional[float] = Field(None, ge=0)
    weighted_value_override_eur: Optional[float] = Field(None, ge=0)
    probability_override: Optional[float] = Field(None, ge=0, le=1)
    forecast_close_month: Optional[str] = None
    owner_user_id: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|archived)$")


class OpportunityCloseRequest(BaseModel):
    """Schema for closing an opportunity"""
    outcome: str = Field(..., pattern="^(won|lost)$")
    won_value_eur: Optional[float] = Field(None, ge=0)
    lost_reason: Optional[str] = None


class OpportunityResponse(BaseModel):
    """Schema for opportunity response"""
    id: str
    account_id: str
    name: Optional[str] = None
    stage_id: str
    stage_detail: Optional[str] = None
    expected_value_eur: float
    weighted_value_override_eur: Optional[float] = None
    probability_override: Optional[float] = None
    forecast_close_month: Optional[str] = None
    close_outcome: str
    close_date: Optional[str] = None
    won_value_eur: Optional[float] = None
    lost_reason: Optional[str] = None
    owner_user_id: Optional[str] = None
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class OpportunityTaskInfo(BaseModel):
    """Task info for opportunity detail"""
    id: str
    title: str
    due_date: Optional[str] = None
    status: str


class OpportunityDetailResponse(BaseModel):
    """Schema for detailed opportunity response with related data"""
    id: str
    account_id: str
    account_name: str
    name: Optional[str] = None
    stage_id: str
    stage_name: str
    stage_key: str
    stage_detail: Optional[str] = None
    expected_value_eur: float
    weighted_value_override_eur: Optional[float] = None
    probability_override: Optional[float] = None
    stage_probability: Optional[float] = None
    forecast_close_month: Optional[str] = None
    close_outcome: str
    close_date: Optional[str] = None
    won_value_eur: Optional[float] = None
    lost_reason: Optional[str] = None
    owner_user_id: Optional[str] = None
    owner_user_name: Optional[str] = None
    status: str
    next_task: Optional[OpportunityTaskInfo] = None
    created_at: str
    updated_at: str


class OpportunityListResponse(BaseModel):
    """Schema for list of opportunities"""
    opportunities: list[OpportunityResponse]
    total: int
