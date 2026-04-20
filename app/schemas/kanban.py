"""
Pydantic schemas for Kanban
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class KanbanNextTask(BaseModel):
    """Next task in opportunity"""
    id: str
    title: str
    due_date: Optional[date] = None
    is_overdue: bool


class KanbanBadges(BaseModel):
    """Badges for opportunity card"""
    lead_source: Optional[str] = None
    region: Optional[str] = None
    customer_type: Optional[str] = None


class KanbanOwner(BaseModel):
    """Owner user info"""
    id: str
    name: str


class KanbanOpportunityItem(BaseModel):
    """Opportunity item in Kanban column"""
    opportunity_id: str
    account_id: str
    account_name: str
    opportunity_name: Optional[str] = None
    expected_value_eur: float
    probability: float
    weighted_value_eur: float
    forecast_close_month: Optional[str] = None
    close_outcome: str
    next_task: Optional[KanbanNextTask] = None
    badges: KanbanBadges
    owner: Optional[KanbanOwner] = None


class KanbanStage(BaseModel):
    """Stage info for Kanban"""
    id: str
    key: str
    name: str
    description: Optional[str] = None
    sort_order: int
    outcome: str


class KanbanColumn(BaseModel):
    """Kanban column with opportunities"""
    stage_id: str
    stage_key: str
    stage_name: str
    opportunities: List[KanbanOpportunityItem]


class KanbanResponse(BaseModel):
    """Complete Kanban board response"""
    stages: List[KanbanStage]
    columns: List[KanbanColumn]


class MoveStageRequest(BaseModel):
    """Request to move opportunity to new stage"""
    new_stage_id: str = Field(..., min_length=1)
    note: Optional[str] = None


class MoveStageResponse(BaseModel):
    """Response after moving stage"""
    success: bool
    message: str
    opportunity_id: str
    new_stage_id: str
    activity_id: str


class CloseOpportunityRequest(BaseModel):
    """Request to close opportunity as won or lost"""
    close_outcome: str = Field(..., pattern="^(won|lost)$")
    close_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    won_value_eur: Optional[float] = Field(None, ge=0)
    lost_reason: Optional[str] = Field(None, min_length=2)  # legacy
    lost_reason_id: Optional[str] = None   # Sprint 4D — FK a cfg_lost_reasons
    lost_reason_detail: Optional[str] = None  # Sprint 4D — texto libre adicional


class CloseOpportunityResponse(BaseModel):
    """Response after closing opportunity"""
    success: bool
    message: str
    opportunity_id: str
    close_outcome: str
    activity_id: str
    outcome_id: Optional[str] = None   # Sprint 5D: ID del registro en opportunity_outcomes
