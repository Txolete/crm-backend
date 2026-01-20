"""
Admin Automations endpoints - PASO 8
Manual execution of automation jobs for testing
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.auth import require_role
from app.automations.jobs import (
    automation_overdue_tasks,
    automation_no_activity,
    automation_proposal_followup,
    run_all_automations
)
from app.automations.email_service import send_daily_task_emails
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/automations", tags=["Admin Automations"])


@router.post("/run")
def run_automation_manual(
    job: str = Query(..., pattern="^(overdue|no_activity|proposal_followup|all|emails)$"),
    current_user: User = Depends(require_role("admin"))
):
    """
    Manually trigger automation jobs (admin only)
    
    PASO 8 - For testing purposes, allows admin to run automations manually
    
    Query params:
    - job: 'overdue' | 'no_activity' | 'proposal_followup' | 'all' | 'emails'
    
    Returns:
    - Results of the job execution (processed, skipped counts)
    """
    logger.info(f"[MANUAL] Admin {current_user.email} triggered job: {job}")
    
    try:
        if job == 'overdue':
            results = automation_overdue_tasks()
            return {
                "success": True,
                "job": "overdue",
                "results": results,
                "triggered_by": current_user.email
            }
        
        elif job == 'no_activity':
            results = automation_no_activity()
            return {
                "success": True,
                "job": "no_activity",
                "results": results,
                "triggered_by": current_user.email
            }
        
        elif job == 'proposal_followup':
            results = automation_proposal_followup()
            return {
                "success": True,
                "job": "proposal_followup",
                "results": results,
                "triggered_by": current_user.email
            }
        
        elif job == 'all':
            results = run_all_automations()
            return {
                "success": True,
                "job": "all",
                "results": results,
                "triggered_by": current_user.email
            }
        
        elif job == 'emails':
            results = send_daily_task_emails()
            return {
                "success": True,
                "job": "emails",
                "results": results,
                "triggered_by": current_user.email
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid job: {job}"
            )
    
    except Exception as e:
        logger.error(f"[MANUAL] Job {job} failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job execution failed: {str(e)}"
        )


@router.get("/status")
def automation_status(
    current_user: User = Depends(require_role("admin"))
):
    """
    Get automation status and configuration
    
    Returns current automation settings and scheduler status
    """
    from app.config import get_settings
    from app.automations.scheduler import scheduler
    
    settings = get_settings()
    
    # Check scheduler status
    scheduler_running = scheduler is not None and scheduler.running
    next_run = None
    
    if scheduler and scheduler.running:
        jobs = scheduler.get_jobs()
        if jobs:
            next_run = jobs[0].next_run_time.isoformat() if jobs[0].next_run_time else None
    
    return {
        "automations_enabled": settings.automations_enabled,
        "scheduler_running": scheduler_running,
        "next_run": next_run,
        "configuration": {
            "run_time": settings.auto_run_time,
            "no_activity_days": settings.auto_no_activity_days,
            "proposal_no_activity_days": settings.auto_proposal_no_activity_days,
            "overdue_dedup_days": settings.auto_overdue_dedup_days,
            "followup_dedup_days": settings.auto_followup_dedup_days
        },
        "email": {
            "enabled": settings.email_enabled,
            "smtp_host": settings.smtp_host,
            "smtp_port": settings.smtp_port,
            "smtp_user": settings.smtp_user[:20] + "..." if settings.smtp_user else None
        }
    }
