"""
Configuration API routes - Simple GET endpoints for frontend
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import (
    CfgStage, CfgStageProbability, CfgRegion, 
    CfgCustomerType, CfgLeadSource, CfgContactRole, CfgTaskTemplate
)
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
