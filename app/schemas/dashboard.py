"""
Pydantic schemas for Dashboard KPIs and Charts
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class DashboardFilters(BaseModel):
    """Active filters"""
    year: int
    lead_source_id: Optional[str] = None
    customer_type_id: Optional[str] = None
    region_id: Optional[str] = None
    owner_user_id: Optional[str] = None
    q: Optional[str] = None


class DashboardTargets(BaseModel):
    """Annual targets"""
    target_pipeline_total: float
    target_pipeline_weighted: float
    target_closed: float


class DashboardKPIs(BaseModel):
    """Current KPIs"""
    pipeline_total_A: float
    pipeline_weighted_B: float
    closed_total_C: float
    conversion_C_over_A_current: Optional[float] = None


class DashboardSeries(BaseModel):
    """Time series data for charts"""
    months: List[str]  # ["Jan", "Feb", ...]
    closed_cum: List[float]  # Cumulative closed by month
    closed_monthly: List[float]  # Monthly closed (not cumulative)
    target_closed_cum: List[float]  # Theoretical cumulative target
    conversion_c_over_a: List[Optional[float]]  # Monthly conversion C/A


class BreakdownItem(BaseModel):
    """Single breakdown item"""
    key: str
    label: str
    value: float


class DashboardBreakdowns(BaseModel):
    """Breakdown data for charts"""
    by_stage: List[BreakdownItem]
    by_lead_source: List[BreakdownItem]


class DashboardSummaryResponse(BaseModel):
    """Complete dashboard summary"""
    year: int
    filters: DashboardFilters
    targets: DashboardTargets
    kpis: DashboardKPIs
    series: DashboardSeries
    breakdowns: DashboardBreakdowns


class TargetsResponse(BaseModel):
    """Targets for a specific year"""
    year: int
    target_pipeline_total: float
    target_pipeline_weighted: float
    target_closed: float
    created_at: str
    updated_at: str


class TargetsUpdateRequest(BaseModel):
    """Request to update targets"""
    target_pipeline_total: float = Field(..., ge=0)
    target_pipeline_weighted: float = Field(..., ge=0)
    target_closed: float = Field(..., ge=0)


class TargetsUpdateResponse(BaseModel):
    """Response after updating targets"""
    success: bool
    message: str
    targets: TargetsResponse
