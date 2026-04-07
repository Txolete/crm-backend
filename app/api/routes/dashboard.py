"""
Dashboard endpoints - Unified
HTML pages + KPIs/Summary API + Targets API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional
from datetime import datetime, date, timezone
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
from app.utils.audit import create_audit_log, generate_id, get_iso_timestamp, get_utc_now
from app.utils.opportunity import calculate_probability, calculate_weighted_value
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Configure Jinja2 templates
templates = Jinja2Templates(directory="app/templates")



# ---------------------------------------------------------------------------
# HTML page endpoints
# ---------------------------------------------------------------------------

@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Serve dashboard HTML page

    **Authentication:** Checked client-side via /auth/me
    If not authenticated, dashboard.js will redirect to /login

    **Permissions:** All authenticated users
    """
    settings = get_settings()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "app_meta": {
                "name": settings.app_name,
                "version": settings.app_version,
                "release": "v1.0",
                "release_date": "2026-01-16",
                "features": [
                    "Dashboard con KPIs (pipeline total/ponderado, pacing)",
                    "Kanban de oportunidades con drag & drop",
                    "Gesti\u00f3n de clientes y contactos",
                    "Importaci\u00f3n desde Excel",
                    "Dashboard de tareas",
                    "Cat\u00e1logos (stages, regiones, tipos, fuentes) auto-cargados"
                ]
            }
        }
    )


@router.get("/config", response_class=HTMLResponse)
async def config_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Serve config management page

    **Permissions:** Admin only (enforced by API and frontend)
    """
    return templates.TemplateResponse(
        "config.html",
        {
            "request": request,
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
                "role": current_user.role
            }
        }
    )


@router.get("/test-won-lost", response_class=HTMLResponse)
async def test_won_lost(request: Request):
    """Test page to diagnose won/lost kanban issues"""
    return templates.TemplateResponse(
        "test_kanban_won_lost.html",
        {"request": request}
    )


@router.get("/test-version", response_class=HTMLResponse)
async def test_version(request: Request):
    """Test page to verify dashboard.js version"""
    return templates.TemplateResponse(
        "test_version.html",
        {"request": request}
    )


# ---------------------------------------------------------------------------
# KPI / Summary API endpoints (formerly dashboard_kpis.py)
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=DashboardSummaryResponse)
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

    **Permissions:** All authenticated users
    """
    # 1. Get or create targets for the year
    target = db.query(Target).filter(Target.year == year).first()

    if not target:
        timestamp = get_utc_now()
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
    base_query = db.query(Opportunity).join(
        Account, Account.id == Opportunity.account_id
    ).filter(
        Opportunity.status == "active"
    )

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

    # Commercial role can only see their own opportunities
    if current_user.role == "commercial":
        base_query = base_query.filter(Opportunity.owner_user_id == current_user.id)

    all_opps = base_query.all()

    # Preload stage probs and stages
    stage_probs = db.query(CfgStageProbability).all()
    stage_probs_map = {sp.stage_id: sp.probability for sp in stage_probs}

    stages = db.query(CfgStage).all()
    stages_map = {s.id: s for s in stages}

    # 3. Calculate KPIs
    kpi_a = sum(
        opp.expected_value_eur
        for opp in all_opps
        if opp.close_outcome == 'open'
    )

    kpi_b = 0.0
    for opp in all_opps:
        if opp.close_outcome == 'open':
            prob = calculate_probability(opp, stage_probs_map, stages_map)
            kpi_b += calculate_weighted_value(opp, prob)

    year_start = datetime(year, 1, 1, tzinfo=timezone.utc)
    year_end = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    kpi_c = sum(
        (opp.won_value_eur if opp.won_value_eur is not None else opp.expected_value_eur)
        for opp in all_opps
        if opp.close_outcome == 'won' and opp.close_date and
           year_start <= opp.close_date <= year_end
    )

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
    closed_monthly = []
    target_closed_cum = []
    conversion_c_over_a = []

    for month_num in range(1, 13):
        last_day = monthrange(year, month_num)[1]
        month_end = datetime(year, month_num, last_day, 23, 59, 59, tzinfo=timezone.utc)
        month_start = datetime(year, month_num, 1, tzinfo=timezone.utc)

        c_cum = sum(
            (opp.won_value_eur if opp.won_value_eur is not None else opp.expected_value_eur)
            for opp in all_opps
            if opp.close_outcome == 'won' and opp.close_date and
               year_start <= opp.close_date <= month_end
        )
        closed_cum.append(c_cum)

        c_monthly = sum(
            (opp.won_value_eur if opp.won_value_eur is not None else opp.expected_value_eur)
            for opp in all_opps
            if opp.close_outcome == 'won' and opp.close_date and
               month_start <= opp.close_date <= month_end
        )
        closed_monthly.append(c_monthly)

        target_cum = target.target_closed * (month_num / 12.0)
        target_closed_cum.append(target_cum)

        a_snapshot = sum(
            opp.expected_value_eur
            for opp in all_opps
            if (opp.created_at and opp.created_at <= month_end and
                (opp.close_outcome == 'open' or
                 (opp.close_date and opp.close_date > month_end)))
        )

        conv = (c_cum / a_snapshot) if a_snapshot > 0 else None
        conversion_c_over_a.append(conv)

    series_data = DashboardSeries(
        months=months_labels,
        closed_cum=closed_cum,
        closed_monthly=closed_monthly,
        target_closed_cum=target_closed_cum,
        conversion_c_over_a=conversion_c_over_a
    )

    # 5. Calculate breakdowns
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
                prob = calculate_probability(opp, stage_probs_map, stages_map)
                weighted = calculate_weighted_value(opp, prob)
                stage_breakdown[stage_key]['value'] += weighted

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

    lead_sources = db.query(CfgLeadSource).all()
    lead_sources_map = {ls.id: ls.name for ls in lead_sources}

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
                prob = calculate_probability(opp, stage_probs_map, stages_map)
                weighted = calculate_weighted_value(opp, prob)
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


# ---------------------------------------------------------------------------
# Targets API endpoints (formerly in dashboard_kpis.py)
# ---------------------------------------------------------------------------

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
        timestamp = get_utc_now()
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
        target.target_pipeline_total = request.target_pipeline_total
        target.target_pipeline_weighted = request.target_pipeline_weighted
        target.target_closed = request.target_closed
        target.updated_at = get_utc_now()
        action_msg = "updated"

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
