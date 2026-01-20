"""
Dashboard KPIs and Charts endpoints
PASO 5 - Dashboard Summary with filters
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional
from datetime import datetime, date
from calendar import monthrange
from app.database import get_db
from app.models.user import User
from app.models.account import Account
from app.models.opportunity import Opportunity
from app.models.config import CfgStage, CfgStageProbability, CfgLeadSource
from app.models.target import Target
from app.schemas.dashboard import (
    DashboardSummaryResponse, DashboardFilters, DashboardTargets,
    DashboardKPIs, DashboardSeries, DashboardBreakdowns, BreakdownItem,
    TargetsResponse, TargetsUpdateRequest, TargetsUpdateResponse
)
from app.utils.auth import get_current_user_from_cookie, require_role
from app.utils.audit import create_audit_log, generate_id, get_iso_timestamp
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Dashboard"])


def calculate_probability_for_opp(opportunity: Opportunity, stage_probs_map: dict, stages_map: dict) -> float:
    """Calculate probability for an opportunity (reused from kanban)"""
    if opportunity.probability_override is not None:
        return opportunity.probability_override
    
    if opportunity.stage_id in stage_probs_map:
        return stage_probs_map[opportunity.stage_id]
    
    default_probs = {
        "new": 0.05, "contacted": 0.10, "qualified": 0.30,
        "proposal": 0.50, "negotiation": 0.70, "won": 1.00, "lost": 0.00
    }
    
    stage = stages_map.get(opportunity.stage_id)
    if stage and stage.key in default_probs:
        return default_probs[stage.key]
    
    return 0.0


def calculate_weighted_value_for_opp(opportunity: Opportunity, probability: float) -> float:
    """Calculate weighted value for an opportunity"""
    if opportunity.weighted_value_override_eur is not None:
        return opportunity.weighted_value_override_eur
    return opportunity.expected_value_eur * probability


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    year: int = Query(default=2026, ge=2020, le=2100),
    lead_source_id: Optional[str] = Query(None),
    customer_type_id: Optional[str] = Query(None),
    region_id: Optional[str] = Query(None),
    owner_user_id: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get dashboard summary with KPIs, series, and breakdowns
    
    **PASO 5** - Complete dashboard data with filters
    
    **Permissions:** All authenticated users
    
    Returns:
    - Annual targets
    - KPIs A/B/C (filtered)
    - Pacing series (monthly)
    - Conversion series (monthly)
    - Breakdowns by stage and lead_source
    """
    # 1. Get or create targets for the year
    target = db.query(Target).filter(Target.year == year).first()
    
    if not target:
        # Create default targets if not exist
        timestamp = get_iso_timestamp()
        target = Target(
            id=generate_id(),
            year=year,
            target_pipeline_total=1000000.0,
            target_pipeline_weighted=500000.0,
            target_closed=300000.0,
            created_at=timestamp,
            updated_at=timestamp
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        logger.info(f"Created default targets for year {year}")
    
    targets_data = DashboardTargets(
        target_pipeline_total=target.target_pipeline_total,
        target_pipeline_weighted=target.target_pipeline_weighted,
        target_closed=target.target_closed
    )
    
    # 2. Build base query with filters
    # Join opportunities with accounts for filtering
    base_query = db.query(Opportunity).join(
        Account, Account.id == Opportunity.account_id
    ).filter(
        Opportunity.status == "active"
    )
    
    # Apply filters
    if lead_source_id:
        base_query = base_query.filter(Account.lead_source_id == lead_source_id)
    
    if customer_type_id:
        base_query = base_query.filter(Account.customer_type_id == customer_type_id)
    
    if region_id:
        base_query = base_query.filter(Account.region_id == region_id)
    
    if owner_user_id:
        base_query = base_query.filter(Opportunity.owner_user_id == owner_user_id)
    
    if q:
        base_query = base_query.filter(Account.name.ilike(f'%{q}%'))
    
    # Get all opportunities (will filter in memory for different metrics)
    all_opps = base_query.all()
    
    # Preload stage probs and stages for probability calculation
    stage_probs = db.query(CfgStageProbability).all()
    stage_probs_map = {sp.stage_id: sp.probability for sp in stage_probs}
    
    stages = db.query(CfgStage).all()
    stages_map = {s.id: s for s in stages}
    
    # 3. Calculate KPIs
    # KPI A: Pipeline Total (open opportunities)
    kpi_a = sum(
        opp.expected_value_eur 
        for opp in all_opps 
        if opp.close_outcome == 'open'
    )
    
    # KPI B: Pipeline Weighted (open opportunities)
    kpi_b = 0.0
    for opp in all_opps:
        if opp.close_outcome == 'open':
            prob = calculate_probability_for_opp(opp, stage_probs_map, stages_map)
            kpi_b += calculate_weighted_value_for_opp(opp, prob)
    
    # KPI C: Closed in year (won opportunities)
    year_start = f"{year}-01-01"
    year_end = f"{year}-12-31"
    
    kpi_c = sum(
        (opp.won_value_eur if opp.won_value_eur is not None else opp.expected_value_eur)
        for opp in all_opps
        if opp.close_outcome == 'won' and opp.close_date and 
           year_start <= opp.close_date <= year_end
    )
    
    # Conversion C/A (current)
    conversion_current = (kpi_c / kpi_a) if kpi_a > 0 else None
    
    kpis_data = DashboardKPIs(
        pipeline_total_A=kpi_a,
        pipeline_weighted_B=kpi_b,
        closed_total_C=kpi_c,
        conversion_C_over_A_current=conversion_current
    )
    
    # 4. Calculate monthly series
    months_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    closed_cum = []
    closed_monthly = []  # NUEVO: cerrado mensual
    target_closed_cum = []
    conversion_c_over_a = []
    
    prev_c_cum = 0  # Para calcular el mensual
    
    for month_num in range(1, 13):  # 1 to 12
        # End of month date
        last_day = monthrange(year, month_num)[1]
        month_end = f"{year}-{month_num:02d}-{last_day:02d}"
        month_start = f"{year}-{month_num:02d}-01"
        
        # Closed cumulative: sum of won up to this month
        c_cum = sum(
            (opp.won_value_eur if opp.won_value_eur is not None else opp.expected_value_eur)
            for opp in all_opps
            if opp.close_outcome == 'won' and opp.close_date and 
               year_start <= opp.close_date <= month_end
        )
        closed_cum.append(c_cum)
        
        # Closed monthly: just this month
        c_monthly = sum(
            (opp.won_value_eur if opp.won_value_eur is not None else opp.expected_value_eur)
            for opp in all_opps
            if opp.close_outcome == 'won' and opp.close_date and 
               month_start <= opp.close_date <= month_end
        )
        closed_monthly.append(c_monthly)
        
        # Target cumulative: linear pacing
        target_cum = target.target_closed * (month_num / 12.0)
        target_closed_cum.append(target_cum)
        
        # Pipeline snapshot at end of month (approximation with current data)
        # A_snapshot: opportunities that existed at end of month and were still open
        a_snapshot = sum(
            opp.expected_value_eur
            for opp in all_opps
            if (opp.created_at and opp.created_at <= month_end and
                (opp.close_outcome == 'open' or 
                 (opp.close_date and opp.close_date > month_end)))
        )
        
        # Conversion: C_cum / A_snapshot
        conv = (c_cum / a_snapshot) if a_snapshot > 0 else None
        conversion_c_over_a.append(conv)
        
        prev_c_cum = c_cum
    
    series_data = DashboardSeries(
        months=months_labels,
        closed_cum=closed_cum,
        closed_monthly=closed_monthly,  # NUEVO
        target_closed_cum=target_closed_cum,
        conversion_c_over_a=conversion_c_over_a
    )
    
    # 5. Calculate breakdowns
    # By stage (using weighted pipeline for OPEN opportunities)
    stage_breakdown = {}
    for opp in all_opps:
        if opp.close_outcome == 'open':
            stage = stages_map.get(opp.stage_id)
            if stage:
                stage_key = stage.key
                if stage_key not in stage_breakdown:
                    stage_breakdown[stage_key] = {
                        'label': stage.name,
                        'value': 0.0
                    }
                prob = calculate_probability_for_opp(opp, stage_probs_map, stages_map)
                weighted = calculate_weighted_value_for_opp(opp, prob)
                stage_breakdown[stage_key]['value'] += weighted
    
    # Add LOST opportunities to breakdown
    lost_total = sum(
        opp.expected_value_eur
        for opp in all_opps
        if opp.close_outcome == 'lost'
    )
    if lost_total > 0:
        stage_breakdown['lost'] = {
            'label': 'Perdido',
            'value': lost_total
        }
    
    by_stage = [
        BreakdownItem(key=k, label=v['label'], value=v['value'])
        for k, v in sorted(stage_breakdown.items(), key=lambda x: x[1]['value'], reverse=True)
    ]
    
    # By lead_source (using weighted pipeline)
    lead_sources = db.query(CfgLeadSource).all()
    lead_sources_map = {ls.id: ls.name for ls in lead_sources}
    
    # Get accounts for current opportunities
    account_ids = list(set(opp.account_id for opp in all_opps))
    accounts = db.query(Account).filter(Account.id.in_(account_ids)).all()
    accounts_map = {acc.id: acc for acc in accounts}
    
    lead_source_breakdown = {}
    for opp in all_opps:
        if opp.close_outcome == 'open':
            account = accounts_map.get(opp.account_id)
            if account and account.lead_source_id:
                ls_name = lead_sources_map.get(account.lead_source_id, "Unknown")
                if ls_name not in lead_source_breakdown:
                    lead_source_breakdown[ls_name] = 0.0
                prob = calculate_probability_for_opp(opp, stage_probs_map, stages_map)
                weighted = calculate_weighted_value_for_opp(opp, prob)
                lead_source_breakdown[ls_name] += weighted
    
    by_lead_source = [
        BreakdownItem(key=name, label=name, value=value)
        for name, value in sorted(lead_source_breakdown.items(), key=lambda x: x[1], reverse=True)
    ]
    
    breakdowns_data = DashboardBreakdowns(
        by_stage=by_stage,
        by_lead_source=by_lead_source
    )
    
    # 6. Build filters object
    filters_data = DashboardFilters(
        year=year,
        lead_source_id=lead_source_id,
        customer_type_id=customer_type_id,
        region_id=region_id,
        owner_user_id=owner_user_id,
        q=q
    )
    
    logger.info(f"Dashboard summary loaded for year {year} with {len(all_opps)} opportunities")
    
    return DashboardSummaryResponse(
        year=year,
        filters=filters_data,
        targets=targets_data,
        kpis=kpis_data,
        series=series_data,
        breakdowns=breakdowns_data
    )


@router.get("/targets", response_model=TargetsResponse)
def get_targets(
    year: int = Query(default=2026, ge=2020, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get targets for a specific year
    
    **Permissions:** All authenticated users
    """
    target = db.query(Target).filter(Target.year == year).first()
    
    if not target:
        # Return default targets if not exist
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No targets found for year {year}"
        )
    
    return TargetsResponse(
        year=target.year,
        target_pipeline_total=target.target_pipeline_total,
        target_pipeline_weighted=target.target_pipeline_weighted,
        target_closed=target.target_closed,
        created_at=target.created_at,
        updated_at=target.updated_at
    )


@router.put("/targets", response_model=TargetsUpdateResponse)
def update_targets(
    year: int = Query(default=2026, ge=2020, le=2100),
    request: TargetsUpdateRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Update targets for a specific year
    
    **Permissions:** admin only
    """
    target = db.query(Target).filter(Target.year == year).first()
    
    if not target:
        # Create new target
        timestamp = get_iso_timestamp()
        target = Target(
            id=generate_id(),
            year=year,
            target_pipeline_total=request.target_pipeline_total,
            target_pipeline_weighted=request.target_pipeline_weighted,
            target_closed=request.target_closed,
            created_at=timestamp,
            updated_at=timestamp
        )
        db.add(target)
        action_msg = "created"
    else:
        # Update existing
        target.target_pipeline_total = request.target_pipeline_total
        target.target_pipeline_weighted = request.target_pipeline_weighted
        target.target_closed = request.target_closed
        target.updated_at = get_iso_timestamp()
        action_msg = "updated"
    
    # Audit log
    create_audit_log(
        db=db,
        entity="targets",
        entity_id=str(year),
        action="update_targets",
        user_id=current_user.id,
        after_data={
            "year": year,
            "target_pipeline_total": request.target_pipeline_total,
            "target_pipeline_weighted": request.target_pipeline_weighted,
            "target_closed": request.target_closed
        }
    )
    
    db.commit()
    db.refresh(target)
    
    logger.info(f"Targets {action_msg} for year {year} by {current_user.email}")
    
    return TargetsUpdateResponse(
        success=True,
        message=f"Targets {action_msg} successfully",
        targets=TargetsResponse(
            year=target.year,
            target_pipeline_total=target.target_pipeline_total,
            target_pipeline_weighted=target.target_pipeline_weighted,
            target_closed=target.target_closed,
            created_at=target.created_at,
            updated_at=target.updated_at
        )
    )
