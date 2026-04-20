"""
Configuration API routes - Simple GET endpoints for frontend
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models import (
    CfgStage, CfgStageProbability, CfgRegion,
    CfgCustomerType, CfgLeadSource, CfgContactRole, CfgTaskTemplate,
    CfgOpportunityType, CfgLostReason, CfgClientMentalState, CfgAiPrompt,
)
from app.models.user import User
from app.utils.auth import get_current_user_from_cookie, require_role
from pydantic import BaseModel

router = APIRouter(prefix="/config", tags=["Configuration"])


# ============================================================================
# SCHEMAS
# ============================================================================

class StageSchema(BaseModel):
    id: str
    key: str
    name: str
    sort_order: int
    outcome: str
    is_terminal: int
    is_active: int
    probability: float = None
    
    class Config:
        from_attributes = True


class RegionSchema(BaseModel):
    id: str
    name: str
    country_code: str
    is_active: int
    sort_order: int
    
    class Config:
        from_attributes = True


class CustomerTypeSchema(BaseModel):
    id: str
    name: str
    is_active: int
    sort_order: int
    
    class Config:
        from_attributes = True


class LeadSourceSchema(BaseModel):
    id: str
    name: str
    category: str = None
    is_active: int
    sort_order: int
    
    class Config:
        from_attributes = True


class ContactRoleSchema(BaseModel):
    id: str
    name: str
    is_active: int
    sort_order: int
    
    class Config:
        from_attributes = True


class TaskTemplateSchema(BaseModel):
    id: str
    name: str
    default_due_days: int = None
    is_active: int
    sort_order: int
    
    class Config:
        from_attributes = True


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/stages", response_model=List[StageSchema])
async def get_stages(db: Session = Depends(get_db)):
    """Get all stages with their probabilities"""
    stages = db.query(CfgStage).order_by(CfgStage.sort_order).all()
    
    # Enrich with probabilities
    result = []
    for stage in stages:
        stage_dict = {
            "id": stage.id,
            "key": stage.key,
            "name": stage.name,
            "sort_order": stage.sort_order,
            "outcome": stage.outcome,
            "is_terminal": stage.is_terminal,
            "is_active": stage.is_active,
            "probability": None
        }
        
        # Get probability
        prob = db.query(CfgStageProbability).filter(
            CfgStageProbability.stage_id == stage.id
        ).first()
        
        if prob:
            stage_dict["probability"] = prob.probability
        
        result.append(stage_dict)
    
    return result


@router.get("/regions", response_model=List[RegionSchema])
async def get_regions(db: Session = Depends(get_db)):
    """Get all regions"""
    return db.query(CfgRegion).order_by(CfgRegion.sort_order).all()


@router.get("/customer-types", response_model=List[CustomerTypeSchema])
async def get_customer_types(db: Session = Depends(get_db)):
    """Get all customer types"""
    return db.query(CfgCustomerType).order_by(CfgCustomerType.sort_order).all()


@router.get("/lead-sources", response_model=List[LeadSourceSchema])
async def get_lead_sources(db: Session = Depends(get_db)):
    """Get all lead sources"""
    return db.query(CfgLeadSource).order_by(CfgLeadSource.sort_order).all()


@router.get("/contact-roles", response_model=List[ContactRoleSchema])
async def get_contact_roles(db: Session = Depends(get_db)):
    """Get all contact roles"""
    return db.query(CfgContactRole).order_by(CfgContactRole.sort_order).all()


@router.get("/task-templates", response_model=List[TaskTemplateSchema])
async def get_task_templates(db: Session = Depends(get_db)):
    """Get all task templates"""
    return db.query(CfgTaskTemplate).order_by(CfgTaskTemplate.sort_order).all()


class OpportunityTypeSchema(BaseModel):
    id: str
    name: str
    is_active: int
    sort_order: int

    class Config:
        from_attributes = True


class LostReasonSchema(BaseModel):
    id: str
    name: str
    is_active: int
    sort_order: int

    class Config:
        from_attributes = True


class ClientMentalStateSchema(BaseModel):
    id: str
    name: str
    is_active: int
    sort_order: int

    class Config:
        from_attributes = True


@router.get("/opportunity-types", response_model=List[OpportunityTypeSchema])
async def get_opportunity_types(db: Session = Depends(get_db)):
    """Get all active opportunity types"""
    return db.query(CfgOpportunityType).filter(CfgOpportunityType.is_active == 1).order_by(CfgOpportunityType.sort_order).all()


@router.get("/lost-reasons", response_model=List[LostReasonSchema])
async def get_lost_reasons(db: Session = Depends(get_db)):
    """Get all active lost reasons"""
    return db.query(CfgLostReason).filter(CfgLostReason.is_active == 1).order_by(CfgLostReason.sort_order).all()


@router.get("/client-mental-states", response_model=List[ClientMentalStateSchema])
async def get_client_mental_states(db: Session = Depends(get_db)):
    """Get all active client mental states"""
    return db.query(CfgClientMentalState).filter(CfgClientMentalState.is_active == 1).order_by(CfgClientMentalState.sort_order).all()


# ============================================================================
# AI PROMPTS — solo admin
# ============================================================================

class AiPromptSchema(BaseModel):
    agent: str
    name: str
    system_prompt: str
    updated_at: Optional[datetime] = None
    updated_by_user_id: Optional[str] = None

    class Config:
        from_attributes = True


class AiPromptUpdate(BaseModel):
    system_prompt: str


_VALID_AGENTS = ('client', 'sales', 'memory')


@router.get("/ai-prompts", response_model=List[AiPromptSchema])
async def get_ai_prompts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Get all AI agent system prompts (admin only)"""
    return db.query(CfgAiPrompt).all()


@router.put("/ai-prompts/{agent}", response_model=AiPromptSchema)
async def update_ai_prompt(
    agent: str,
    body: AiPromptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Update system prompt for a specific agent (admin only)"""
    if agent not in _VALID_AGENTS:
        raise HTTPException(status_code=400, detail=f"Agent must be one of {_VALID_AGENTS}")

    row = db.query(CfgAiPrompt).filter(CfgAiPrompt.agent == agent).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Agent '{agent}' not found in cfg_ai_prompts")

    row.system_prompt = body.system_prompt
    row.updated_at = datetime.now(timezone.utc)
    row.updated_by_user_id = current_user.id
    db.commit()
    db.refresh(row)
    return row
