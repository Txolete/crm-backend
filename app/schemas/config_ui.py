"""
Schemas for Config Management UI
PASO 7 - Admin config panel
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional


# === REGIONS ===
class RegionBase(BaseModel):
    name: str
    country_code: str = "ES"
    is_active: bool = True
    sort_order: int = 0


class RegionCreate(RegionBase):
    pass


class RegionUpdate(BaseModel):
    name: Optional[str] = None
    country_code: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class RegionResponse(RegionBase):
    id: str
    created_at: str
    updated_at: str


# === CUSTOMER TYPES ===
class CustomerTypeBase(BaseModel):
    name: str
    is_active: bool = True
    sort_order: int = 0


class CustomerTypeCreate(CustomerTypeBase):
    pass


class CustomerTypeUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class CustomerTypeResponse(CustomerTypeBase):
    id: str
    created_at: str
    updated_at: str


# === LEAD SOURCES ===
class LeadSourceBase(BaseModel):
    name: str
    category: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class LeadSourceCreate(LeadSourceBase):
    pass


class LeadSourceUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class LeadSourceResponse(LeadSourceBase):
    id: str
    created_at: str
    updated_at: str


# === CONTACT ROLES ===
class ContactRoleBase(BaseModel):
    name: str
    is_active: bool = True
    sort_order: int = 0


class ContactRoleCreate(ContactRoleBase):
    pass


class ContactRoleUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ContactRoleResponse(ContactRoleBase):
    id: str
    created_at: str
    updated_at: str


# === TASK TEMPLATES ===
class TaskTemplateBase(BaseModel):
    name: str
    default_due_days: Optional[int] = None
    is_active: bool = True
    sort_order: int = 0


class TaskTemplateCreate(TaskTemplateBase):
    pass


class TaskTemplateUpdate(BaseModel):
    name: Optional[str] = None
    default_due_days: Optional[int] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class TaskTemplateResponse(TaskTemplateBase):
    id: str
    created_at: str
    updated_at: str


# === STAGES ===
class StageBase(BaseModel):
    key: str
    name: str
    sort_order: int
    outcome: str  # open, won, lost
    is_terminal: bool = False
    is_active: bool = True
    
    @validator('outcome')
    def validate_outcome(cls, v):
        if v not in ['open', 'won', 'lost']:
            raise ValueError('outcome must be open, won, or lost')
        return v


class StageCreate(StageBase):
    pass


class StageUpdate(BaseModel):
    key: Optional[str] = None
    name: Optional[str] = None
    sort_order: Optional[int] = None
    outcome: Optional[str] = None
    is_terminal: Optional[bool] = None
    is_active: Optional[bool] = None
    
    @validator('outcome')
    def validate_outcome(cls, v):
        if v is not None and v not in ['open', 'won', 'lost']:
            raise ValueError('outcome must be open, won, or lost')
        return v


class StageResponse(StageBase):
    id: str
    created_at: str
    updated_at: str


# === STAGE PROBABILITIES ===
class StageProbabilityBase(BaseModel):
    stage_id: str
    probability: float = Field(..., ge=0.0, le=1.0)


class StageProbabilityCreate(StageProbabilityBase):
    pass


class StageProbabilityUpdate(BaseModel):
    probability: float = Field(..., ge=0.0, le=1.0)


class StageProbabilityResponse(StageProbabilityBase):
    created_at: str
    updated_at: str
    stage_name: Optional[str] = None


# === LIST RESPONSES ===
class RegionsListResponse(BaseModel):
    regions: List[RegionResponse]


class CustomerTypesListResponse(BaseModel):
    customer_types: List[CustomerTypeResponse]


class LeadSourcesListResponse(BaseModel):
    lead_sources: List[LeadSourceResponse]


class ContactRolesListResponse(BaseModel):
    contact_roles: List[ContactRoleResponse]


class TaskTemplatesListResponse(BaseModel):
    task_templates: List[TaskTemplateResponse]


class StagesListResponse(BaseModel):
    stages: List[StageResponse]


class StageProbabilitiesListResponse(BaseModel):
    stage_probabilities: List[StageProbabilityResponse]


# === USAGE CHECK ===
class UsageCheckResponse(BaseModel):
    in_use: bool
    count: int
    message: str
