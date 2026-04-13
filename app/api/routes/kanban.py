"""
Kanban endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.user import User
from app.models.account import Account
from app.models.config import (
    CfgStage, CfgStageProbability, CfgLeadSource, 
    CfgRegion, CfgCustomerType
)
from app.models.opportunity import Opportunity, Activity
from app.schemas.kanban import (
    KanbanResponse, KanbanColumn, KanbanStage, KanbanOpportunityItem,
    KanbanNextTask, KanbanBadges, KanbanOwner,
    MoveStageRequest, MoveStageResponse,
    CloseOpportunityRequest, CloseOpportunityResponse
)
from app.utils.auth import get_current_user_from_cookie, require_role
from app.utils.opportunity import get_next_open_task, calculate_probability, calculate_weighted_value
from app.utils.audit import create_audit_log, generate_id, get_iso_timestamp, get_utc_now, ENTITY_OPPORTUNITIES
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kanban", tags=["Kanban"])



@router.get("", response_model=KanbanResponse)
def get_kanban(
    q: Optional[str] = Query(None, description="Search by account name"),
    stage_id: Optional[str] = Query(None),
    lead_source_id: Optional[str] = Query(None),
    region_id: Optional[str] = Query(None),
    customer_type_id: Optional[str] = Query(None),
    owner_user_id: Optional[str] = Query(None),
    include_closed: bool = Query(True, description="Include won/lost stages"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get Kanban board data
    
    **Permissions:** All authenticated users
    
    HOTFIX 4.1: Optimized with eager loading to reduce N+1 queries
    
    Returns stages and opportunities grouped by stage with all necessary data
    for rendering Kanban cards
    """
    # Get all stages ordered by sort_order
    stages_query = db.query(CfgStage).filter(CfgStage.is_active == 1)
    
    if not include_closed:
        # Exclude won/lost stages
        stages_query = stages_query.filter(
            CfgStage.outcome == 'open'
        )
    
    stages = stages_query.order_by(CfgStage.sort_order).all()
    
    # Build stages list for response AND create map for later use
    stages_map = {stage.id: stage for stage in stages}
    stages_list = [
        KanbanStage(
            id=stage.id,
            key=stage.key,
            name=stage.name,
            description=stage.description,
            sort_order=stage.sort_order,
            outcome=stage.outcome
        )
        for stage in stages
    ]
    
    # OPTIMIZATION: Preload stage probabilities into a map
    stage_probs = db.query(CfgStageProbability).all()
    stage_probs_map = {sp.stage_id: sp.probability for sp in stage_probs}
    
    # OPTIMIZATION: Preload config data into maps
    cfg_lead_sources = db.query(CfgLeadSource).all()
    lead_sources_map = {ls.id: ls.name for ls in cfg_lead_sources}
    
    cfg_regions = db.query(CfgRegion).all()
    regions_map = {r.id: r.name for r in cfg_regions}
    
    cfg_customer_types = db.query(CfgCustomerType).all()
    customer_types_map = {ct.id: ct.name for ct in cfg_customer_types}
    
    # OPTIMIZATION: Query opportunities with eager loading of accounts and owners
    # This eliminates N+1 queries by loading related data in a single query
    opps_query = db.query(Opportunity).filter(
        Opportunity.status == "active"
    )
    
    # Apply opportunity-level filters
    if stage_id:
        opps_query = opps_query.filter(Opportunity.stage_id == stage_id)
    
    if owner_user_id:
        opps_query = opps_query.filter(Opportunity.owner_user_id == owner_user_id)

    # Commercial role can only see their own opportunities
    if current_user.role == "commercial":
        opps_query = opps_query.filter(Opportunity.owner_user_id == current_user.id)

    # Execute query and get opportunities
    opportunities = opps_query.all()
    
    # OPTIMIZATION: Batch load accounts
    account_ids = list(set(opp.account_id for opp in opportunities))
    accounts = db.query(Account).filter(Account.id.in_(account_ids)).all()
    accounts_map = {acc.id: acc for acc in accounts}
    
    # Apply account-level filters (post-query filtering)
    if q or lead_source_id or region_id or customer_type_id:
        filtered_opps = []
        for opp in opportunities:
            account = accounts_map.get(opp.account_id)
            if not account:
                continue
            
            # Search filter
            if q and q.lower() not in account.name.lower():
                continue
            
            # Lead source filter
            if lead_source_id and account.lead_source_id != lead_source_id:
                continue
            
            # Region filter
            if region_id and account.region_id != region_id:
                continue
            
            # Customer type filter
            if customer_type_id and account.customer_type_id != customer_type_id:
                continue
            
            filtered_opps.append(opp)
        
        opportunities = filtered_opps
    
    # OPTIMIZATION: Batch load owners
    owner_ids = list(set(opp.owner_user_id for opp in opportunities if opp.owner_user_id))
    if owner_ids:
        owners = db.query(User).filter(User.id.in_(owner_ids)).all()
        owners_map = {owner.id: owner for owner in owners}
    else:
        owners_map = {}
    
    # Build columns by stage
    columns = []
    today = date.today()
    
    # Build columns by stage
    columns = []
    today = date.today()
    
    for stage in stages:
        items = []
        
        # Get opportunities for this stage
        stage_opps = [opp for opp in opportunities if opp.stage_id == stage.id]
        
        for opp in stage_opps:
            # Get account from preloaded map (OPTIMIZED)
            account = accounts_map.get(opp.account_id)
            if not account:
                continue
            
            # Calculate probability (OPTIMIZED - uses preloaded maps)
            probability = calculate_probability(opp, stage_probs_map, stages_map)
            
            # Calculate weighted value
            weighted_value = calculate_weighted_value(opp, probability)
            
            # Get next task (still uses helper function)
            next_task_obj = get_next_open_task(db, opp.id)
            next_task = None
            if next_task_obj:
                is_overdue = False
                if next_task_obj.due_date:
                    is_overdue = next_task_obj.due_date < today
                
                next_task = KanbanNextTask(
                    id=next_task_obj.id,
                    title=next_task_obj.title,
                    due_date=next_task_obj.due_date,
                    is_overdue=is_overdue
                )
            
            # Get badges from preloaded maps (OPTIMIZED)
            lead_source_name = lead_sources_map.get(account.lead_source_id)
            region_name = regions_map.get(account.region_id)
            customer_type_name = customer_types_map.get(account.customer_type_id)
            
            badges = KanbanBadges(
                lead_source=lead_source_name,
                region=region_name,
                customer_type=customer_type_name
            )
            
            # Get owner from preloaded map (OPTIMIZED)
            owner = None
            if opp.owner_user_id and opp.owner_user_id in owners_map:
                owner_user = owners_map[opp.owner_user_id]
                owner = KanbanOwner(
                    id=owner_user.id,
                    name=owner_user.name
                )
            
            # Create item
            item = KanbanOpportunityItem(
                opportunity_id=opp.id,
                account_id=account.id,
                account_name=account.name,
                opportunity_name=opp.name,
                expected_value_eur=opp.expected_value_eur,
                probability=probability,
                weighted_value_eur=weighted_value,
                forecast_close_month=opp.forecast_close_month,
                close_outcome=opp.close_outcome,
                next_task=next_task,
                badges=badges,
                owner=owner
            )
            
            items.append(item)
        
        # Sort items within column
        # Priority: 1) overdue tasks, 2) tasks by due_date, 3) no task
        def sort_key(item):
            if item.next_task:
                if item.next_task.is_overdue:
                    # Overdue tasks first
                    return (0, item.next_task.due_date or "9999-12-31")
                elif item.next_task.due_date:
                    # Tasks with due_date, sorted by date
                    return (1, item.next_task.due_date)
                else:
                    # Tasks without due_date
                    return (2, "9999-12-31")
            else:
                # No task - goes to end
                return (3, "9999-12-31")
        
        items.sort(key=sort_key)
        
        # Add column
        columns.append(
            KanbanColumn(
                stage_id=stage.id,
                stage_key=stage.key,
                stage_name=stage.name,
                opportunities=items
            )
        )
    
    logger.info(f"Kanban loaded: {len(opportunities)} opportunities across {len(columns)} columns (OPTIMIZED)")
    
    return KanbanResponse(
        stages=stages_list,
        columns=columns
    )


@router.post("/{opportunity_id}/move-stage", response_model=MoveStageResponse)
def move_stage(
    opportunity_id: str,
    request: MoveStageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Move opportunity to a new stage (drag & drop)
    
    **Permissions:** admin, sales
    
    Rules:
    - Cannot move to won/lost via drag (use close endpoint)
    - Creates activity with type "status_change"
    - Creates audit log
    """
    # Get opportunity
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    # Get old stage
    old_stage = db.query(CfgStage).filter(CfgStage.id == opportunity.stage_id).first()
    if not old_stage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current stage not found"
        )
    
    # Get new stage
    new_stage = db.query(CfgStage).filter(CfgStage.id == request.new_stage_id).first()
    if not new_stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="New stage not found"
        )
    
    # Prevent moving to won/lost via drag
    if new_stage.outcome in ('won', 'lost'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot move to won/lost stage via drag. Use close endpoint instead."
        )
    
    # Store before state
    before_data = {
        "stage_id": opportunity.stage_id,
        "stage_key": old_stage.key
    }
    
    # Update stage
    opportunity.stage_id = request.new_stage_id
    opportunity.updated_at = get_utc_now()
    
    # Create activity
    timestamp = get_utc_now()
    summary = f"Stage changed: {old_stage.key} -> {new_stage.key}"
    if request.note:
        summary += f" | Note: {request.note}"
    
    activity = Activity(
        id=generate_id(),
        opportunity_id=opportunity.id,
        type="status_change",
        occurred_at=timestamp,
        summary=summary,
        created_by_user_id=current_user.id,
        created_at=timestamp
    )
    
    db.add(activity)
    
    # Store after state
    after_data = {
        "stage_id": opportunity.stage_id,
        "stage_key": new_stage.key
    }
    
    # Create audit log
    create_audit_log(
        db=db,
        entity=ENTITY_OPPORTUNITIES,
        entity_id=opportunity.id,
        action="move_stage",
        user_id=current_user.id,
        before_data=before_data,
        after_data=after_data
    )
    
    # Single commit
    db.commit()
    db.refresh(opportunity)
    db.refresh(activity)
    
    logger.info(f"Opportunity {opportunity.id} moved from {old_stage.key} to {new_stage.key} by {current_user.email}")
    
    return MoveStageResponse(
        success=True,
        message=f"Opportunity moved to {new_stage.name}",
        opportunity_id=opportunity.id,
        new_stage_id=new_stage.id,
        activity_id=activity.id
    )


@router.post("/{opportunity_id}/close", response_model=CloseOpportunityResponse)
def close_opportunity(
    opportunity_id: str,
    request: CloseOpportunityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Close opportunity as WON or LOST
    
    **Permissions:** admin, sales
    
    **HOTFIX 4.1 - Part B**
    
    Rules:
    - Sets close_outcome to 'won' or 'lost'
    - Sets close_date
    - Moves to appropriate stage (won/lost)
    - For won: captures won_value_eur (defaults to expected_value_eur)
    - For lost: requires lost_reason
    - Creates activity with type "status_change"
    - Creates audit log with action "close"
    - Single commit transaction
    """
    # Get opportunity
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    # Check if already closed
    if opportunity.close_outcome in ('won', 'lost'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Opportunity already closed as {opportunity.close_outcome}"
        )
    
    # Validate request based on outcome
    if request.close_outcome == 'won':
        # For won, won_value_eur defaults to expected_value_eur if not provided
        won_value = request.won_value_eur if request.won_value_eur is not None else opportunity.expected_value_eur
    elif request.close_outcome == 'lost':
        # Sprint 4D: lost_reason_id es obligatorio para nuevas pérdidas
        if not request.lost_reason_id:
            # Fallback legacy: aceptar lost_reason (texto libre) si no viene lost_reason_id
            if not request.lost_reason or len(request.lost_reason.strip()) < 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="lost_reason_id is required to close as lost"
                )
        won_value = None
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="close_outcome must be 'won' or 'lost'"
        )
    
    # Find the target stage (won or lost)
    target_stage = db.query(CfgStage).filter(CfgStage.key == request.close_outcome).first()
    
    if not target_stage:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stage with key '{request.close_outcome}' not found in configuration"
        )
    
    # Store before state
    before_data = {
        "stage_id": opportunity.stage_id,
        "close_outcome": opportunity.close_outcome,
        "close_date": opportunity.close_date,
        "won_value_eur": opportunity.won_value_eur,
        "lost_reason": opportunity.lost_reason
    }
    
    # Update opportunity
    opportunity.close_outcome = request.close_outcome
    opportunity.close_date = request.close_date
    opportunity.stage_id = target_stage.id
    
    if request.close_outcome == 'won':
        opportunity.won_value_eur = won_value
        opportunity.lost_reason = None
        opportunity.lost_reason_id = None
        opportunity.lost_reason_detail = None
        opportunity.probability_override = None  # B5/B6: limpiar override al ganar, probabilidad = 100%
    else:  # lost
        opportunity.lost_reason = request.lost_reason  # legacy
        opportunity.lost_reason_id = request.lost_reason_id
        opportunity.lost_reason_detail = request.lost_reason_detail
        opportunity.won_value_eur = None
    
    opportunity.updated_at = get_utc_now()
    
    # Create activity
    timestamp = get_utc_now()
    summary = f"Closed as {request.close_outcome.upper()}"
    if request.close_outcome == 'won' and won_value:
        summary += f" - Value: €{won_value:,.2f}"
    elif request.close_outcome == 'lost' and request.lost_reason:
        summary += f" - Reason: {request.lost_reason}"
    
    activity = Activity(
        id=generate_id(),
        opportunity_id=opportunity.id,
        type="status_change",
        occurred_at=timestamp,
        summary=summary,
        created_by_user_id=current_user.id,
        created_at=timestamp
    )
    
    db.add(activity)
    
    # Store after state
    after_data = {
        "stage_id": opportunity.stage_id,
        "close_outcome": opportunity.close_outcome,
        "close_date": opportunity.close_date,
        "won_value_eur": opportunity.won_value_eur,
        "lost_reason": opportunity.lost_reason
    }
    
    # Create audit log
    create_audit_log(
        db=db,
        entity=ENTITY_OPPORTUNITIES,
        entity_id=opportunity.id,
        action="close",
        user_id=current_user.id,
        before_data=before_data,
        after_data=after_data
    )
    
    # Single commit
    db.commit()
    db.refresh(opportunity)
    db.refresh(activity)
    
    logger.info(f"Opportunity {opportunity.id} closed as {request.close_outcome} by {current_user.email}")
    
    return CloseOpportunityResponse(
        success=True,
        message=f"Opportunity closed as {request.close_outcome.upper()}",
        opportunity_id=opportunity.id,
        close_outcome=request.close_outcome,
        activity_id=activity.id
    )
