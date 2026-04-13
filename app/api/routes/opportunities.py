"""
Opportunity endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.opportunity import Opportunity
from app.schemas.opportunity import (
    OpportunityCreate, OpportunityUpdate, OpportunityCloseRequest,
    OpportunityResponse, OpportunityListResponse,
    OpportunityDetailResponse, OpportunityTaskInfo
)
from app.utils.auth import get_current_user_from_cookie, require_role
from app.utils.audit import create_audit_log, generate_id, get_iso_timestamp, get_utc_now, ENTITY_OPPORTUNITIES
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])


@router.get("", response_model=OpportunityListResponse)
def list_opportunities(
    status: Optional[str] = Query("active", pattern="^(active|archived|all)$"),
    stage_id: Optional[str] = Query(None),
    close_outcome: Optional[str] = Query(None, pattern="^(open|won|lost)$"),
    owner_user_id: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Search in name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    List opportunities with filters
    
    **Permissions:** All authenticated users
    """
    query = db.query(Opportunity)
    
    # Filter by status
    if status == "active":
        query = query.filter(Opportunity.status == "active")
    elif status == "archived":
        query = query.filter(Opportunity.status == "archived")
    
    # Filter by stage
    if stage_id:
        query = query.filter(Opportunity.stage_id == stage_id)
    
    # Filter by close_outcome
    if close_outcome:
        query = query.filter(Opportunity.close_outcome == close_outcome)
    
    # Filter by owner
    if owner_user_id:
        query = query.filter(Opportunity.owner_user_id == owner_user_id)

    # Commercial role can only see their own opportunities
    if current_user.role == "commercial":
        query = query.filter(Opportunity.owner_user_id == current_user.id)

    # Search by name
    if q:
        query = query.filter(Opportunity.name.ilike(f"%{q}%"))
    
    opportunities = query.all()
    
    return OpportunityListResponse(
        opportunities=[OpportunityResponse.model_validate(opp) for opp in opportunities],
        total=len(opportunities)
    )


@router.post("", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    opportunity_data: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Create a new opportunity
    
    **Permissions:** admin, sales
    """
    timestamp = get_utc_now()
    
    new_opportunity = Opportunity(
        id=generate_id(),
        account_id=opportunity_data.account_id,
        name=opportunity_data.name,
        stage_id=opportunity_data.stage_id,
        stage_detail=opportunity_data.stage_detail,
        expected_value_eur=opportunity_data.expected_value_eur,
        weighted_value_override_eur=opportunity_data.weighted_value_override_eur,
        probability_override=opportunity_data.probability_override,
        forecast_close_month=opportunity_data.forecast_close_month,
        close_outcome="open",  # Always starts as open
        close_date=None,
        won_value_eur=None,
        lost_reason=None,
        owner_user_id=opportunity_data.owner_user_id,
        status="active",
        created_at=timestamp,
        updated_at=timestamp
    )
    
    db.add(new_opportunity)
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_OPPORTUNITIES,
        entity_id=new_opportunity.id,
        action="create",
        user_id=current_user.id,
        after_data={
            "account_id": new_opportunity.account_id,
            "stage_id": new_opportunity.stage_id,
            "expected_value_eur": new_opportunity.expected_value_eur,
            "close_outcome": new_opportunity.close_outcome,
            "status": new_opportunity.status
        }
    )
    
    # Create initial activity
    from app.api.routes.activities import create_activity_auto
    from app.models.config import CfgStage
    
    stage = db.query(CfgStage).filter(CfgStage.id == new_opportunity.stage_id).first()
    stage_name = stage.name if stage else new_opportunity.stage_id
    
    create_activity_auto(
        db=db,
        opportunity_id=new_opportunity.id,
        activity_type="status_change",
        summary=f"Oportunidad creada en estado: {stage_name}",
        user_id=current_user.id
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(new_opportunity)
    
    logger.info(f"Opportunity created: {new_opportunity.id} by {current_user.email}")
    
    return OpportunityResponse.model_validate(new_opportunity)


@router.get("/{opportunity_id}", response_model=OpportunityDetailResponse)
def get_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get opportunity by ID with all related data
    
    **Permissions:** All authenticated users
    """
    from app.models.account import Account
    from app.models.config import CfgStage, CfgStageProbability, CfgOpportunityType, CfgLostReason, CfgClientMentalState
    from app.models.user import User as UserModel
    from app.models.opportunity import Task  # Task está en opportunity.py

    # Get opportunity
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()

    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )

    # Get account
    account = db.query(Account).filter(Account.id == opportunity.account_id).first()
    account_name = account.name if account else "Unknown"

    # Get stage
    stage = db.query(CfgStage).filter(CfgStage.id == opportunity.stage_id).first()
    stage_name = stage.name if stage else "Unknown"
    stage_key = stage.key if stage else ""

    # Get stage probability
    stage_prob = db.query(CfgStageProbability).filter(
        CfgStageProbability.stage_id == opportunity.stage_id
    ).first()
    stage_probability = stage_prob.probability if stage_prob else None

    # Get owner
    owner_name = None
    if opportunity.owner_user_id:
        owner = db.query(UserModel).filter(UserModel.id == opportunity.owner_user_id).first()
        owner_name = owner.name if owner else None

    # Get next open task
    next_task = None
    task = db.query(Task).filter(
        Task.opportunity_id == opportunity_id,
        Task.status == "open"
    ).order_by(Task.due_date).first()

    if task:
        next_task = OpportunityTaskInfo(
            id=task.id,
            title=task.title,
            due_date=task.due_date,
            status=task.status
        )

    # Sprint 4B — nombres de las relaciones nuevas
    opportunity_type_name = None
    if opportunity.opportunity_type_id:
        ot = db.query(CfgOpportunityType).filter(CfgOpportunityType.id == opportunity.opportunity_type_id).first()
        opportunity_type_name = ot.name if ot else None

    lost_reason_name = None
    if opportunity.lost_reason_id:
        lr = db.query(CfgLostReason).filter(CfgLostReason.id == opportunity.lost_reason_id).first()
        lost_reason_name = lr.name if lr else None

    client_mental_state_name = None
    if opportunity.client_mental_state_id:
        ms = db.query(CfgClientMentalState).filter(CfgClientMentalState.id == opportunity.client_mental_state_id).first()
        client_mental_state_name = ms.name if ms else None

    # Build response
    return OpportunityDetailResponse(
        id=opportunity.id,
        account_id=opportunity.account_id,
        account_name=account_name,
        name=opportunity.name,
        stage_id=opportunity.stage_id,
        stage_name=stage_name,
        stage_key=stage_key,
        stage_detail=opportunity.stage_detail,
        expected_value_eur=opportunity.expected_value_eur,
        weighted_value_override_eur=opportunity.weighted_value_override_eur,
        probability_override=opportunity.probability_override,
        stage_probability=stage_probability,
        forecast_close_month=opportunity.forecast_close_month,
        close_outcome=opportunity.close_outcome,
        close_date=opportunity.close_date,
        won_value_eur=opportunity.won_value_eur,
        lost_reason=opportunity.lost_reason,
        owner_user_id=opportunity.owner_user_id,
        owner_user_name=owner_name,
        status=opportunity.status,
        next_task=next_task,
        opportunity_type_id=opportunity.opportunity_type_id,
        opportunity_type_name=opportunity_type_name,
        client_mental_state_id=opportunity.client_mental_state_id,
        client_mental_state_name=client_mental_state_name,
        strategic_objective=opportunity.strategic_objective,
        next_strategic_action=opportunity.next_strategic_action,
        executive_summary=opportunity.executive_summary,
        lost_reason_id=opportunity.lost_reason_id,
        lost_reason_name=lost_reason_name,
        lost_reason_detail=opportunity.lost_reason_detail,
        hold_reason=opportunity.hold_reason,
        chatgpt_thread_id=opportunity.chatgpt_thread_id,
        chatgpt_url=opportunity.chatgpt_url,
        created_at=opportunity.created_at,
        updated_at=opportunity.updated_at
    )


@router.put("/{opportunity_id}", response_model=OpportunityResponse)
def update_opportunity(
    opportunity_id: str,
    opportunity_data: OpportunityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Update opportunity
    
    **Permissions:** admin, sales
    
    **Note:** To change stage, use this endpoint. Moving stage creates an activity.
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    # Store before state
    before_data = {
        "stage_id": opportunity.stage_id,
        "expected_value_eur": opportunity.expected_value_eur,
        "owner_user_id": opportunity.owner_user_id
    }
    
    # Track if stage changed (for activity creation)
    stage_changed = False
    old_stage_id = opportunity.stage_id
    
    # Update fields
    if opportunity_data.name is not None:
        opportunity.name = opportunity_data.name
    if opportunity_data.stage_id is not None:
        if opportunity_data.stage_id != opportunity.stage_id:
            stage_changed = True
            old_stage_id = opportunity.stage_id
        opportunity.stage_id = opportunity_data.stage_id
        
        # Check if new stage is terminal (won/lost) - AUTO-CLOSE
        from app.models.config import CfgStage
        new_stage = db.query(CfgStage).filter(CfgStage.id == opportunity_data.stage_id).first()
        if new_stage and new_stage.outcome in ('won', 'lost'):
            # Auto-close the opportunity
            opportunity.close_outcome = new_stage.outcome
            opportunity.close_date = datetime.now(timezone.utc)
            
            if new_stage.outcome == 'won':
                # Set won_value_eur (use expected_value if not set)
                if opportunity.won_value_eur is None:
                    opportunity.won_value_eur = opportunity.expected_value_eur
            else:
                # Lost: clear won_value_eur
                opportunity.won_value_eur = None
            
            logger.info(f"[AUTO-CLOSE] Opportunity {opportunity.id} automatically closed as {new_stage.outcome}")
        elif new_stage and new_stage.outcome == 'open':
            # Re-opening a closed opportunity
            if opportunity.close_outcome in ('won', 'lost'):
                opportunity.close_outcome = 'open'
                opportunity.close_date = None
                opportunity.won_value_eur = None
                logger.info(f"[RE-OPEN] Opportunity {opportunity.id} re-opened from closed state")
    
    if opportunity_data.stage_detail is not None:
        opportunity.stage_detail = opportunity_data.stage_detail
    if opportunity_data.expected_value_eur is not None:
        opportunity.expected_value_eur = opportunity_data.expected_value_eur
    if opportunity_data.weighted_value_override_eur is not None:
        opportunity.weighted_value_override_eur = opportunity_data.weighted_value_override_eur
    if opportunity_data.probability_override is not None:
        opportunity.probability_override = opportunity_data.probability_override
    if opportunity_data.forecast_close_month is not None:
        opportunity.forecast_close_month = opportunity_data.forecast_close_month
    if opportunity_data.owner_user_id is not None:
        opportunity.owner_user_id = opportunity_data.owner_user_id
    if opportunity_data.status is not None:
        opportunity.status = opportunity_data.status
        logger.info(f"[STATUS] Opportunity {opportunity.id} status changed to {opportunity_data.status}")
    
    opportunity.updated_at = get_utc_now()
    
    # Store after state
    after_data = {
        "stage_id": opportunity.stage_id,
        "expected_value_eur": opportunity.expected_value_eur,
        "owner_user_id": opportunity.owner_user_id
    }
    
    # Audit log
    action = "move_stage" if stage_changed else "update"
    create_audit_log(
        db=db,
        entity=ENTITY_OPPORTUNITIES,
        entity_id=opportunity.id,
        action=action,
        user_id=current_user.id,
        before_data=before_data,
        after_data=after_data
    )
    
    # Create activity for stage change
    if stage_changed:
        from app.api.routes.activities import create_activity_auto
        from app.models.config import CfgStage
        
        # Get stage names
        old_stage = db.query(CfgStage).filter(CfgStage.id == old_stage_id).first()
        new_stage = db.query(CfgStage).filter(CfgStage.id == opportunity.stage_id).first()
        
        old_name = old_stage.name if old_stage else old_stage_id
        new_name = new_stage.name if new_stage else opportunity.stage_id
        
        create_activity_auto(
            db=db,
            opportunity_id=opportunity.id,
            activity_type="status_change",
            summary=f"Estado cambiado: {old_name} → {new_name}",
            user_id=current_user.id
        )
        
        # Also create activity for won/lost
        if new_stage and new_stage.outcome == 'won':
            create_activity_auto(
                db=db,
                opportunity_id=opportunity.id,
                activity_type="won",
                summary=f"¡Oportunidad GANADA! 🎉 Valor: {opportunity.won_value_eur}€",
                user_id=current_user.id
            )
        elif new_stage and new_stage.outcome == 'lost':
            create_activity_auto(
                db=db,
                opportunity_id=opportunity.id,
                activity_type="lost",
                summary=f"Oportunidad perdida. Motivo: {opportunity.lost_reason or 'No especificado'}",
                user_id=current_user.id
            )
    
    # Single commit at the end
    db.commit()
    db.refresh(opportunity)
    
    logger.info(f"Opportunity updated: {opportunity.id} by {current_user.email} (stage_changed={stage_changed})")
    
    return OpportunityResponse.model_validate(opportunity)


@router.post("/{opportunity_id}/close", response_model=OpportunityResponse)
def close_opportunity(
    opportunity_id: str,
    close_data: OpportunityCloseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Close opportunity as won or lost
    
    **Permissions:** admin, sales
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    if opportunity.close_outcome != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Opportunity already closed as {opportunity.close_outcome}"
        )
    
    # Store before state
    before_data = {
        "close_outcome": opportunity.close_outcome,
        "close_date": opportunity.close_date
    }
    
    # Update close fields
    opportunity.close_outcome = close_data.outcome
    opportunity.close_date = datetime.now(timezone.utc)

    if close_data.outcome == "won":
        opportunity.won_value_eur = close_data.won_value_eur or opportunity.expected_value_eur
        opportunity.lost_reason = None
    else:  # lost
        opportunity.won_value_eur = None
        opportunity.lost_reason = close_data.lost_reason
    
    opportunity.updated_at = get_utc_now()
    
    # Store after state
    after_data = {
        "close_outcome": opportunity.close_outcome,
        "close_date": opportunity.close_date,
        "won_value_eur": opportunity.won_value_eur,
        "lost_reason": opportunity.lost_reason
    }
    
    # Audit log
    action = "close_won" if close_data.outcome == "won" else "close_lost"
    create_audit_log(
        db=db,
        entity=ENTITY_OPPORTUNITIES,
        entity_id=opportunity.id,
        action=action,
        user_id=current_user.id,
        before_data=before_data,
        after_data=after_data
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(opportunity)
    
    logger.info(f"Opportunity closed as {close_data.outcome}: {opportunity.id} by {current_user.email}")
    
    return OpportunityResponse.model_validate(opportunity)


@router.post("/{opportunity_id}/archive", response_model=OpportunityResponse)
def archive_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Archive opportunity (logical deletion)
    
    **Permissions:** admin, sales
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    if opportunity.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Opportunity already archived"
        )
    
    opportunity.status = "archived"
    opportunity.updated_at = get_utc_now()
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_OPPORTUNITIES,
        entity_id=opportunity.id,
        action="archive",
        user_id=current_user.id,
        after_data={
            "account_id": opportunity.account_id,
            "status": "archived"
        }
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(opportunity)
    
    logger.info(f"Opportunity archived: {opportunity.id} by {current_user.email}")
    
    return OpportunityResponse.model_validate(opportunity)


@router.post("/{opportunity_id}/restore", response_model=OpportunityResponse)
def restore_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Restore archived opportunity
    
    **Permissions:** admin, sales
    """
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    if opportunity.status == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Opportunity already active"
        )
    
    opportunity.status = "active"
    opportunity.updated_at = get_utc_now()
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_OPPORTUNITIES,
        entity_id=opportunity.id,
        action="restore",
        user_id=current_user.id,
        after_data={
            "account_id": opportunity.account_id,
            "status": "active"
        }
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(opportunity)
    
    logger.info(f"Opportunity restored: {opportunity.id} by {current_user.email}")
    
    return OpportunityResponse.model_validate(opportunity)
