"""
Config Management UI endpoints
PASO 7 - Admin panel for cfg_* tables
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.account import Account
from app.models.opportunity import Opportunity, Task
from app.models.config import (
    CfgRegion, CfgCustomerType, CfgLeadSource,
    CfgContactRole, CfgTaskTemplate, CfgStage, CfgStageProbability
)
from app.schemas.config_ui import *
from app.utils.auth import require_role
from app.utils.audit import create_audit_log, generate_id, get_iso_timestamp, get_utc_now
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config-ui", tags=["Config UI"])


# ============================================================================
# REGIONS
# ============================================================================

@router.get("/regions", response_model=RegionsListResponse)
def list_regions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """List all regions (admin only)"""
    regions = db.query(CfgRegion).order_by(CfgRegion.sort_order, CfgRegion.name).all()
    return RegionsListResponse(regions=[RegionResponse(**r.__dict__) for r in regions])


@router.post("/regions", response_model=RegionResponse)
def create_region(
    request: RegionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Create new region"""
    # Check duplicate name
    existing = db.query(CfgRegion).filter(CfgRegion.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Region '{request.name}' already exists"
        )
    
    timestamp = get_utc_now()
    region = CfgRegion(
        id=generate_id(),
        name=request.name,
        country_code=request.country_code,
        is_active=int(request.is_active),
        sort_order=request.sort_order,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    db.add(region)

    create_audit_log(
        db=db,
        entity="config",
        entity_id=region.id,
        action="create_region",
        user_id=current_user.id,
        after_data={"name": region.name}
    )
    db.commit()
    db.refresh(region)

    logger.info(f"Region created: {region.name} by {current_user.email}")
    return RegionResponse(**region.__dict__)


@router.put("/regions/{region_id}", response_model=RegionResponse)
def update_region(
    region_id: str,
    request: RegionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Update region"""
    region = db.query(CfgRegion).filter(CfgRegion.id == region_id).first()
    if not region:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    
    before_data = {"name": region.name, "is_active": region.is_active}
    
    if request.name is not None:
        # Check duplicate
        existing = db.query(CfgRegion).filter(
            CfgRegion.name == request.name,
            CfgRegion.id != region_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Region '{request.name}' already exists"
            )
        region.name = request.name
    
    if request.country_code is not None:
        region.country_code = request.country_code
    if request.is_active is not None:
        region.is_active = int(request.is_active)
    if request.sort_order is not None:
        region.sort_order = request.sort_order
    
    region.updated_at = get_utc_now()

    create_audit_log(
        db=db,
        entity="config",
        entity_id=region.id,
        action="update_region",
        user_id=current_user.id,
        before_data=before_data,
        after_data={"name": region.name, "is_active": region.is_active}
    )
    db.commit()
    db.refresh(region)

    logger.info(f"Region updated: {region.name} by {current_user.email}")
    return RegionResponse(**region.__dict__)


@router.delete("/regions/{region_id}")
def deactivate_region(
    region_id: str,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Deactivate region (soft delete)"""
    region = db.query(CfgRegion).filter(CfgRegion.id == region_id).first()
    if not region:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    
    # HOTFIX 7.1: Check if in use (only active accounts)
    usage_count = db.query(func.count(Account.id)).filter(
        Account.region_id == region_id,
        Account.status == 'active'
    ).scalar()
    
    if usage_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "IN_USE",
                "message": f"Esta provincia está en uso por {usage_count} cuenta(s) activa(s).",
                "in_use_count": usage_count,
                "entity": "regions",
                "id": region_id
            }
        )
    
    region.is_active = 0
    region.updated_at = get_utc_now()
    
    db.commit()
    
    create_audit_log(
        db=db,
        entity="config",
        entity_id=region.id,
        action="deactivate_region_forced" if force else "deactivate_region",
        user_id=current_user.id,
        after_data={"name": region.name, "is_active": False, "forced": force}
    )
    db.commit()
    
    logger.info(f"Region deactivated: {region.name} by {current_user.email} (forced={force})")
    return {"success": True, "message": f"Region '{region.name}' deactivated", "forced": force}


@router.get("/regions/{region_id}/usage", response_model=UsageCheckResponse)
def check_region_usage(
    region_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Check if region is in use"""
    count = db.query(func.count(Account.id)).filter(
        Account.region_id == region_id
    ).scalar()
    
    return UsageCheckResponse(
        in_use=count > 0,
        count=count,
        message=f"Region is used by {count} account(s)" if count > 0 else "Region is not in use"
    )


# ============================================================================
# CUSTOMER TYPES
# ============================================================================

@router.get("/customer-types", response_model=CustomerTypesListResponse)
def list_customer_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """List all customer types"""
    items = db.query(CfgCustomerType).order_by(CfgCustomerType.sort_order, CfgCustomerType.name).all()
    return CustomerTypesListResponse(customer_types=[CustomerTypeResponse(**i.__dict__) for i in items])


@router.post("/customer-types", response_model=CustomerTypeResponse)
def create_customer_type(
    request: CustomerTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Create new customer type"""
    existing = db.query(CfgCustomerType).filter(CfgCustomerType.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer type '{request.name}' already exists"
        )
    
    timestamp = get_utc_now()
    item = CfgCustomerType(
        id=generate_id(),
        name=request.name,
        is_active=int(request.is_active),
        sort_order=request.sort_order,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    db.add(item)

    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.id,
        action="create_customer_type",
        user_id=current_user.id,
        after_data={"name": item.name}
    )
    db.commit()
    db.refresh(item)

    return CustomerTypeResponse(**item.__dict__)


@router.put("/customer-types/{item_id}", response_model=CustomerTypeResponse)
def update_customer_type(
    item_id: str,
    request: CustomerTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Update customer type"""
    item = db.query(CfgCustomerType).filter(CfgCustomerType.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer type not found")
    
    if request.name is not None:
        existing = db.query(CfgCustomerType).filter(
            CfgCustomerType.name == request.name,
            CfgCustomerType.id != item_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer type '{request.name}' already exists"
            )
        item.name = request.name
    
    if request.is_active is not None:
        item.is_active = int(request.is_active)
    if request.sort_order is not None:
        item.sort_order = request.sort_order
    
    item.updated_at = get_utc_now()

    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.id,
        action="update_customer_type",
        user_id=current_user.id,
        after_data={"name": item.name, "is_active": item.is_active}
    )
    db.commit()
    db.refresh(item)

    return CustomerTypeResponse(**item.__dict__)


@router.delete("/customer-types/{item_id}")
def deactivate_customer_type(
    item_id: str,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Deactivate customer type"""
    item = db.query(CfgCustomerType).filter(CfgCustomerType.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer type not found")
    
    # HOTFIX 7.1: Check if in use (only active accounts)
    usage_count = db.query(func.count(Account.id)).filter(
        Account.customer_type_id == item_id,
        Account.status == 'active'
    ).scalar()
    
    if usage_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "IN_USE",
                "message": f"Este tipo de cliente está en uso por {usage_count} cuenta(s) activa(s).",
                "in_use_count": usage_count,
                "entity": "customer_types",
                "id": item_id
            }
        )
    
    item.is_active = 0
    item.updated_at = get_utc_now()
    db.commit()
    
    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.id,
        action="deactivate_customer_type_forced" if force else "deactivate_customer_type",
        user_id=current_user.id,
        after_data={"name": item.name, "is_active": False, "forced": force}
    )
    db.commit()
    
    return {"success": True, "message": f"Customer type '{item.name}' deactivated", "forced": force}


@router.get("/customer-types/{item_id}/usage", response_model=UsageCheckResponse)
def check_customer_type_usage(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Check if customer type is in use"""
    count = db.query(func.count(Account.id)).filter(
        Account.customer_type_id == item_id
    ).scalar()
    
    return UsageCheckResponse(
        in_use=count > 0,
        count=count,
        message=f"Customer type is used by {count} account(s)" if count > 0 else "Customer type is not in use"
    )


# ============================================================================
# LEAD SOURCES
# ============================================================================

@router.get("/lead-sources", response_model=LeadSourcesListResponse)
def list_lead_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """List all lead sources"""
    items = db.query(CfgLeadSource).order_by(CfgLeadSource.sort_order, CfgLeadSource.name).all()
    return LeadSourcesListResponse(lead_sources=[LeadSourceResponse(**i.__dict__) for i in items])


@router.post("/lead-sources", response_model=LeadSourceResponse)
def create_lead_source(
    request: LeadSourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Create new lead source"""
    existing = db.query(CfgLeadSource).filter(CfgLeadSource.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lead source '{request.name}' already exists"
        )
    
    timestamp = get_utc_now()
    item = CfgLeadSource(
        id=generate_id(),
        name=request.name,
        category=request.category,
        is_active=int(request.is_active),
        sort_order=request.sort_order,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    db.add(item)

    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.id,
        action="create_lead_source",
        user_id=current_user.id,
        after_data={"name": item.name}
    )
    db.commit()
    db.refresh(item)

    return LeadSourceResponse(**item.__dict__)


@router.put("/lead-sources/{item_id}", response_model=LeadSourceResponse)
def update_lead_source(
    item_id: str,
    request: LeadSourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Update lead source"""
    item = db.query(CfgLeadSource).filter(CfgLeadSource.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead source not found")
    
    if request.name is not None:
        existing = db.query(CfgLeadSource).filter(
            CfgLeadSource.name == request.name,
            CfgLeadSource.id != item_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lead source '{request.name}' already exists"
            )
        item.name = request.name
    
    if request.category is not None:
        item.category = request.category
    if request.is_active is not None:
        item.is_active = int(request.is_active)
    if request.sort_order is not None:
        item.sort_order = request.sort_order
    
    item.updated_at = get_utc_now()

    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.id,
        action="update_lead_source",
        user_id=current_user.id,
        after_data={"name": item.name}
    )
    db.commit()
    db.refresh(item)

    return LeadSourceResponse(**item.__dict__)


@router.delete("/lead-sources/{item_id}")
def deactivate_lead_source(
    item_id: str,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Deactivate lead source"""
    item = db.query(CfgLeadSource).filter(CfgLeadSource.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead source not found")
    
    # HOTFIX 7.1: Check if in use (only active accounts)
    usage_count = db.query(func.count(Account.id)).filter(
        Account.lead_source_id == item_id,
        Account.status == 'active'
    ).scalar()
    
    if usage_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "IN_USE",
                "message": f"Este canal está en uso por {usage_count} cuenta(s) activa(s).",
                "in_use_count": usage_count,
                "entity": "lead_sources",
                "id": item_id
            }
        )
    
    item.is_active = 0
    item.updated_at = get_utc_now()
    db.commit()
    
    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.id,
        action="deactivate_lead_source_forced" if force else "deactivate_lead_source",
        user_id=current_user.id,
        after_data={"name": item.name, "is_active": False, "forced": force}
    )
    db.commit()
    
    return {"success": True, "message": f"Lead source '{item.name}' deactivated", "forced": force}


# Continue in next part...


# ============================================================================
# CONTACT ROLES
# ============================================================================

@router.get("/contact-roles", response_model=ContactRolesListResponse)
def list_contact_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """List all contact roles"""
    from app.models.account import Contact
    items = db.query(CfgContactRole).order_by(CfgContactRole.sort_order, CfgContactRole.name).all()
    return ContactRolesListResponse(contact_roles=[ContactRoleResponse(**i.__dict__) for i in items])


@router.post("/contact-roles", response_model=ContactRoleResponse)
def create_contact_role(
    request: ContactRoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Create new contact role"""
    existing = db.query(CfgContactRole).filter(CfgContactRole.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Contact role '{request.name}' already exists"
        )
    
    timestamp = get_utc_now()
    item = CfgContactRole(
        id=generate_id(),
        name=request.name,
        is_active=int(request.is_active),
        sort_order=request.sort_order,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    db.add(item)

    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.id,
        action="create_contact_role",
        user_id=current_user.id,
        after_data={"name": item.name}
    )
    db.commit()
    db.refresh(item)

    return ContactRoleResponse(**item.__dict__)


@router.put("/contact-roles/{item_id}", response_model=ContactRoleResponse)
def update_contact_role(
    item_id: str,
    request: ContactRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Update contact role"""
    item = db.query(CfgContactRole).filter(CfgContactRole.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact role not found")
    
    if request.name is not None:
        existing = db.query(CfgContactRole).filter(
            CfgContactRole.name == request.name,
            CfgContactRole.id != item_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contact role '{request.name}' already exists"
            )
        item.name = request.name
    
    if request.is_active is not None:
        item.is_active = int(request.is_active)
    if request.sort_order is not None:
        item.sort_order = request.sort_order
    
    item.updated_at = get_utc_now()

    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.id,
        action="update_contact_role",
        user_id=current_user.id,
        after_data={"name": item.name}
    )
    db.commit()
    db.refresh(item)

    return ContactRoleResponse(**item.__dict__)


@router.delete("/contact-roles/{item_id}")
def deactivate_contact_role(
    item_id: str,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Deactivate contact role"""
    from app.models.account import Contact
    item = db.query(CfgContactRole).filter(CfgContactRole.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact role not found")
    
    # HOTFIX 7.1: Check if in use (only active contacts)
    usage_count = db.query(func.count(Contact.id)).filter(
        Contact.contact_role_id == item_id,
        Contact.status == 'active'
    ).scalar()
    
    if usage_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "IN_USE",
                "message": f"Este rol está en uso por {usage_count} contacto(s) activo(s).",
                "in_use_count": usage_count,
                "entity": "contact_roles",
                "id": item_id
            }
        )
    
    item.is_active = 0
    item.updated_at = get_utc_now()
    db.commit()
    
    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.id,
        action="deactivate_contact_role_forced" if force else "deactivate_contact_role",
        user_id=current_user.id,
        after_data={"name": item.name, "is_active": False, "forced": force}
    )
    db.commit()
    
    return {"success": True, "message": f"Contact role '{item.name}' deactivated", "forced": force}


# ============================================================================
# TASK TEMPLATES
# ============================================================================

@router.get("/task-templates", response_model=TaskTemplatesListResponse)
def list_task_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """List all task templates"""
    items = db.query(CfgTaskTemplate).order_by(CfgTaskTemplate.sort_order, CfgTaskTemplate.name).all()
    return TaskTemplatesListResponse(task_templates=[TaskTemplateResponse(**i.__dict__) for i in items])


@router.post("/task-templates", response_model=TaskTemplateResponse)
def create_task_template(
    request: TaskTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Create new task template"""
    existing = db.query(CfgTaskTemplate).filter(CfgTaskTemplate.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task template '{request.name}' already exists"
        )
    
    timestamp = get_utc_now()
    item = CfgTaskTemplate(
        id=generate_id(),
        name=request.name,
        default_due_days=request.default_due_days,
        is_active=int(request.is_active),
        sort_order=request.sort_order,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    db.add(item)

    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.id,
        action="create_task_template",
        user_id=current_user.id,
        after_data={"name": item.name}
    )
    db.commit()
    db.refresh(item)

    return TaskTemplateResponse(**item.__dict__)


@router.put("/task-templates/{item_id}", response_model=TaskTemplateResponse)
def update_task_template(
    item_id: str,
    request: TaskTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Update task template"""
    item = db.query(CfgTaskTemplate).filter(CfgTaskTemplate.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task template not found")
    
    if request.name is not None:
        existing = db.query(CfgTaskTemplate).filter(
            CfgTaskTemplate.name == request.name,
            CfgTaskTemplate.id != item_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task template '{request.name}' already exists"
            )
        item.name = request.name
    
    if request.default_due_days is not None:
        item.default_due_days = request.default_due_days
    if request.is_active is not None:
        item.is_active = int(request.is_active)
    if request.sort_order is not None:
        item.sort_order = request.sort_order
    
    item.updated_at = get_utc_now()

    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.id,
        action="update_task_template",
        user_id=current_user.id,
        after_data={"name": item.name}
    )
    db.commit()
    db.refresh(item)

    return TaskTemplateResponse(**item.__dict__)


@router.delete("/task-templates/{item_id}")
def deactivate_task_template(
    item_id: str,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Deactivate task template"""
    item = db.query(CfgTaskTemplate).filter(CfgTaskTemplate.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task template not found")
    
    # HOTFIX 7.1: Check if in use (tasks with this template)
    usage_count = db.query(func.count(Task.id)).filter(
        Task.task_template_id == item_id
    ).scalar()
    
    if usage_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "IN_USE",
                "message": f"Esta plantilla está en uso por {usage_count} tarea(s).",
                "in_use_count": usage_count,
                "entity": "task_templates",
                "id": item_id
            }
        )
    
    item.is_active = 0
    item.updated_at = get_utc_now()
    db.commit()
    
    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.id,
        action="deactivate_task_template_forced" if force else "deactivate_task_template",
        user_id=current_user.id,
        after_data={"name": item.name, "is_active": False, "forced": force}
    )
    db.commit()
    
    return {"success": True, "message": f"Task template '{item.name}' deactivated", "forced": force}


# ============================================================================
# STAGES
# ============================================================================

@router.get("/stages", response_model=StagesListResponse)
def list_stages(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    List all stages
    
    HOTFIX 7.1: Always ordered by sort_order ASC for Kanban consistency
    """
    items = db.query(CfgStage).order_by(CfgStage.sort_order.asc()).all()
    return StagesListResponse(stages=[StageResponse(**i.__dict__) for i in items])


@router.post("/stages", response_model=StageResponse)
def create_stage(
    request: StageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Create new stage"""
    existing = db.query(CfgStage).filter(CfgStage.key == request.key).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stage key '{request.key}' already exists"
        )
    
    timestamp = get_utc_now()
    item = CfgStage(
        id=generate_id(),
        key=request.key,
        name=request.name,
        sort_order=request.sort_order,
        outcome=request.outcome,
        is_terminal=int(request.is_terminal),
        is_active=int(request.is_active),
        created_at=timestamp,
        updated_at=timestamp
    )
    
    db.add(item)

    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.id,
        action="create_stage",
        user_id=current_user.id,
        after_data={"key": item.key, "name": item.name}
    )
    db.commit()
    db.refresh(item)

    return StageResponse(**item.__dict__)


@router.put("/stages/{item_id}", response_model=StageResponse)
def update_stage(
    item_id: str,
    request: StageUpdate,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Update stage"""
    item = db.query(CfgStage).filter(CfgStage.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
    
    # HOTFIX 7.1: Check if outcome is changing and stage is in use
    if request.outcome is not None and request.outcome != item.outcome:
        usage_count = db.query(func.count(Opportunity.id)).filter(
            Opportunity.stage_id == item_id,
            Opportunity.status == 'active'
        ).scalar()
        
        if usage_count > 0 and not force:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "IN_USE",
                    "message": f"Esta etapa está en uso por {usage_count} oportunidad(es) activa(s). Cambiar outcome puede afectar cálculos.",
                    "in_use_count": usage_count,
                    "entity": "stages",
                    "id": item_id,
                    "change_type": "outcome"
                }
            )
    
    # HOTFIX 7.1: Check if marking as terminal or inactive
    if (request.is_terminal is not None and request.is_terminal and not item.is_terminal) or \
       (request.is_active is not None and not request.is_active and item.is_active):
        usage_count = db.query(func.count(Opportunity.id)).filter(
            Opportunity.stage_id == item_id,
            Opportunity.status == 'active'
        ).scalar()
        
        if usage_count > 0 and not force:
            change = "terminal" if request.is_terminal else "inactive"
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "IN_USE",
                    "message": f"Esta etapa está en uso por {usage_count} oportunidad(es) activa(s).",
                    "in_use_count": usage_count,
                    "entity": "stages",
                    "id": item_id,
                    "change_type": change
                }
            )
    
    if request.key is not None:
        existing = db.query(CfgStage).filter(
            CfgStage.key == request.key,
            CfgStage.id != item_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stage key '{request.key}' already exists"
            )
        item.key = request.key
    
    if request.name is not None:
        item.name = request.name
    if request.sort_order is not None:
        item.sort_order = request.sort_order
    if request.outcome is not None:
        item.outcome = request.outcome
    if request.is_terminal is not None:
        item.is_terminal = int(request.is_terminal)
    if request.is_active is not None:
        item.is_active = int(request.is_active)
    
    item.updated_at = get_utc_now()

    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.id,
        action="update_stage_forced" if force else "update_stage",
        user_id=current_user.id,
        after_data={"key": item.key, "name": item.name, "outcome": item.outcome, "forced": force}
    )
    db.commit()
    db.refresh(item)

    return StageResponse(**item.__dict__)


@router.delete("/stages/{item_id}")
def deactivate_stage(
    item_id: str,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Deactivate stage"""
    item = db.query(CfgStage).filter(CfgStage.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
    
    # HOTFIX 7.1: Check if in use (only active opportunities)
    usage_count = db.query(func.count(Opportunity.id)).filter(
        Opportunity.stage_id == item_id,
        Opportunity.status == 'active'
    ).scalar()
    
    if usage_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "IN_USE",
                "message": f"Esta etapa está en uso por {usage_count} oportunidad(es) activa(s). Desactivarla puede romper el Kanban.",
                "in_use_count": usage_count,
                "entity": "stages",
                "id": item_id
            }
        )
    
    item.is_active = 0
    item.updated_at = get_utc_now()
    db.commit()
    
    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.id,
        action="deactivate_stage_forced" if force else "deactivate_stage",
        user_id=current_user.id,
        after_data={"key": item.key, "is_active": False, "forced": force}
    )
    db.commit()
    
    return {"success": True, "message": f"Stage '{item.name}' deactivated", "forced": force}


# ============================================================================
# STAGE PROBABILITIES
# ============================================================================

@router.get("/stage-probabilities", response_model=StageProbabilitiesListResponse)
def list_stage_probabilities(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """List all stage probabilities"""
    items = db.query(CfgStageProbability).all()
    
    # Enrich with stage name
    result = []
    for item in items:
        stage = db.query(CfgStage).filter(CfgStage.id == item.stage_id).first()
        result.append(StageProbabilityResponse(
            stage_id=item.stage_id,
            probability=item.probability,
            created_at=item.created_at,
            updated_at=item.updated_at,
            stage_name=stage.name if stage else None
        ))
    
    return StageProbabilitiesListResponse(stage_probabilities=result)


@router.post("/stage-probabilities", response_model=StageProbabilityResponse)
def create_stage_probability(
    request: StageProbabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Create/update stage probability"""
    # Check if stage exists
    stage = db.query(CfgStage).filter(CfgStage.id == request.stage_id).first()
    if not stage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
    
    # Check if probability already exists
    existing = db.query(CfgStageProbability).filter(
        CfgStageProbability.stage_id == request.stage_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Probability for stage '{stage.name}' already exists. Use PUT to update."
        )
    
    timestamp = get_utc_now()
    item = CfgStageProbability(
        stage_id=request.stage_id,
        probability=request.probability,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    db.add(item)

    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.stage_id,
        action="create_stage_probability",
        user_id=current_user.id,
        after_data={"stage_id": item.stage_id, "probability": item.probability}
    )
    db.commit()
    
    return StageProbabilityResponse(
        stage_id=item.stage_id,
        probability=item.probability,
        created_at=item.created_at,
        updated_at=item.updated_at,
        stage_name=stage.name
    )


@router.put("/stage-probabilities/{stage_id}", response_model=StageProbabilityResponse)
def update_stage_probability(
    stage_id: str,
    request: StageProbabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Update stage probability"""
    item = db.query(CfgStageProbability).filter(
        CfgStageProbability.stage_id == stage_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage probability not found")
    
    stage = db.query(CfgStage).filter(CfgStage.id == stage_id).first()
    
    item.probability = request.probability
    item.updated_at = get_utc_now()
    
    db.commit()
    db.refresh(item)
    
    create_audit_log(
        db=db,
        entity="config",
        entity_id=item.stage_id,
        action="update_stage_probability",
        user_id=current_user.id,
        after_data={"stage_id": item.stage_id, "probability": item.probability}
    )
    db.commit()
    
    return StageProbabilityResponse(
        stage_id=item.stage_id,
        probability=item.probability,
        created_at=item.created_at,
        updated_at=item.updated_at,
        stage_name=stage.name if stage else None
    )


@router.delete("/stage-probabilities/{stage_id}")
def delete_stage_probability(
    stage_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Delete stage probability"""
    item = db.query(CfgStageProbability).filter(
        CfgStageProbability.stage_id == stage_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage probability not found")
    
    db.delete(item)
    db.commit()
    
    create_audit_log(
        db=db,
        entity="config",
        entity_id=stage_id,
        action="delete_stage_probability",
        user_id=current_user.id,
        after_data={"stage_id": stage_id}
    )
    db.commit()
    
    return {"success": True, "message": "Stage probability deleted"}
