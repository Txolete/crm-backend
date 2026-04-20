"""
Automation Jobs - PASO 8
Daily automated tasks for CRM
"""
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.database import SessionLocal
from app.models.opportunity import Opportunity, Task, Activity
from app.models.account import Account
from app.models.config import CfgStage
from app.utils.audit import create_audit_log, generate_id, get_iso_timestamp, get_utc_now
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

settings = get_settings()


def get_today() -> date:
    """Get today's date"""
    return date.today()


def get_today_str() -> str:
    """Get today's date as YYYY-MM-DD string (legacy compat)"""
    return date.today().isoformat()


def parse_date_str(date_str: str) -> datetime:
    """Parse YYYY-MM-DD string to datetime"""
    return datetime.fromisoformat(date_str) if date_str else None


# ============================================================================
# AUTOMATION A: OVERDUE TASKS DETECTION
# ============================================================================

def automation_overdue_tasks():
    """
    Detect overdue tasks and create system activity
    
    Condition:
    - tasks.status="open"
    - tasks.due_date IS NOT NULL
    - tasks.due_date < today
    
    Action:
    - Create activity type="system" in opportunity
    - Audit log action="auto_overdue"
    
    Dedupe:
    - No repeat if activity system exists with "task_id=<id>" 
      in last AUTO_OVERDUE_DEDUP_DAYS
    """
    db = SessionLocal()
    today = get_today()
    dedup_days = settings.auto_overdue_dedup_days
    dedup_cutoff = datetime.now(timezone.utc) - timedelta(days=dedup_days)
    
    try:
        # Find overdue tasks
        overdue_tasks = db.query(Task).filter(
            Task.status == 'open',
            Task.due_date.isnot(None),
            Task.due_date < today
        ).all()
        
        processed = 0
        skipped = 0
        
        for task in overdue_tasks:
            # Tasks linked only to an account (no opportunity) cannot create
            # an Activity (opportunity_id NOT NULL) — skip them silently
            if not task.opportunity_id:
                skipped += 1
                continue

            # Check dedupe: look for existing system activity with this task_id
            task_marker = f"task_id={task.id}"
            existing = db.query(Activity).filter(
                Activity.opportunity_id == task.opportunity_id,
                Activity.type == 'system',
                Activity.summary.like(f"%{task_marker}%"),
                Activity.occurred_at >= dedup_cutoff
            ).first()

            if existing:
                skipped += 1
                continue

            # Create system activity
            activity = Activity(
                id=generate_id(),
                opportunity_id=task.opportunity_id,
                type='system',
                occurred_at=get_utc_now(),
                summary=f"Task overdue: {task.title} (due {task.due_date}) [task_id={task.id}]",
                created_by_user_id=None,  # System
                created_at=get_utc_now()
            )
            db.add(activity)
            
            # Audit log
            create_audit_log(
                db=db,
                entity="tasks",
                entity_id=task.id,
                action="auto_overdue",
                user_id=None,  # System
                after_data={
                    "task_id": task.id,
                    "title": task.title,
                    "due_date": task.due_date,
                    "opportunity_id": task.opportunity_id
                }
            )
            
            processed += 1
        
        db.commit()
        
        logger.info(f"[AUTOMATION A] Overdue tasks: {processed} processed, {skipped} skipped (deduped)")
        return {"processed": processed, "skipped": skipped}
        
    except Exception as e:
        db.rollback()
        logger.error(f"[AUTOMATION A] Error: {e}")
        raise
    finally:
        db.close()


# ============================================================================
# AUTOMATION B: NO ACTIVITY X DAYS
# ============================================================================

def automation_no_activity():
    """
    Create follow-up task for opportunities with no activity in X days
    
    Condition:
    - opportunities.status='active' AND close_outcome='open'
    - last activity occurred_at <= today - X (X = AUTO_NO_ACTIVITY_DAYS)
    
    Action:
    - If NO task open "Seguimiento pendiente" in last AUTO_FOLLOWUP_DEDUP_DAYS:
        - Create task: title="Seguimiento pendiente", due_date=today+3
        - Create activity system
        - Audit log action="auto_followup_task"
    """
    db = SessionLocal()
    today_dt = datetime.now(timezone.utc)
    no_activity_days = settings.auto_no_activity_days
    dedup_days = settings.auto_followup_dedup_days

    cutoff_date = today_dt - timedelta(days=no_activity_days)
    dedup_cutoff = today_dt - timedelta(days=dedup_days)

    try:
        # Find opportunities with no recent activity
        # Subquery: last activity per opportunity
        last_activity_subq = db.query(
            Activity.opportunity_id,
            func.max(Activity.occurred_at).label('last_activity')
        ).group_by(Activity.opportunity_id).subquery()
        
        # Opportunities: active, open, last activity before cutoff
        opportunities = db.query(Opportunity).outerjoin(
            last_activity_subq,
            Opportunity.id == last_activity_subq.c.opportunity_id
        ).filter(
            Opportunity.status == 'active',
            Opportunity.close_outcome == 'open',
            # Last activity is old OR no activity at all
            func.coalesce(last_activity_subq.c.last_activity, datetime(1900, 1, 1, tzinfo=timezone.utc)) <= cutoff_date
        ).all()
        
        processed = 0
        skipped = 0
        
        for opp in opportunities:
            # Check dedupe: task "Seguimiento pendiente" open in last dedup_days
            existing_task = db.query(Task).filter(
                Task.opportunity_id == opp.id,
                Task.title == 'Seguimiento pendiente',
                Task.status == 'open',
                Task.created_at >= dedup_cutoff
            ).first()
            
            if existing_task:
                skipped += 1
                continue
            
            # Create task
            due_date = (today_dt + timedelta(days=3)).date()
            task = Task(
                id=generate_id(),
                opportunity_id=opp.id,
                task_template_id=None,
                title='Seguimiento pendiente',
                due_date=due_date,
                status='open',
                assigned_to_user_id=opp.owner_user_id,
                created_at=get_utc_now(),
                updated_at=get_utc_now()
            )
            db.add(task)
            
            # Create system activity
            activity = Activity(
                id=generate_id(),
                opportunity_id=opp.id,
                type='system',
                occurred_at=get_utc_now(),
                summary=f"Auto follow-up created (no activity in {no_activity_days} days)",
                created_by_user_id=None,
                created_at=get_utc_now()
            )
            db.add(activity)
            
            # Audit log
            create_audit_log(
                db=db,
                entity="opportunities",
                entity_id=opp.id,
                action="auto_followup_task",
                user_id=None,
                after_data={
                    "opportunity_id": opp.id,
                    "task_id": task.id,
                    "no_activity_days": no_activity_days
                }
            )
            
            processed += 1
        
        db.commit()
        
        logger.info(f"[AUTOMATION B] No activity: {processed} processed, {skipped} skipped (deduped)")
        return {"processed": processed, "skipped": skipped}
        
    except Exception as e:
        db.rollback()
        logger.error(f"[AUTOMATION B] Error: {e}")
        raise
    finally:
        db.close()


# ============================================================================
# AUTOMATION C: PROPOSAL NO FOLLOW-UP Y DAYS
# ============================================================================

def automation_proposal_followup():
    """
    Create follow-up task for proposals with no activity in Y days
    
    Condition:
    - stage key = "proposal"
    - close_outcome='open' AND status='active'
    - last activity <= today - Y (Y = AUTO_PROPOSAL_NO_ACTIVITY_DAYS)
    
    Action:
    - If NO task open "Seguimiento propuesta":
        - Create task: title="Seguimiento propuesta", due_date=today+2
        - Create activity system
        - Audit log action="auto_proposal_followup"
    """
    db = SessionLocal()
    today_dt = datetime.now(timezone.utc)
    no_activity_days = settings.auto_proposal_no_activity_days
    dedup_days = settings.auto_followup_dedup_days

    cutoff_date = today_dt - timedelta(days=no_activity_days)
    dedup_cutoff = today_dt - timedelta(days=dedup_days)
    
    try:
        # Find proposal stage
        proposal_stage = db.query(CfgStage).filter(CfgStage.key == 'proposal').first()
        if not proposal_stage:
            logger.warning("[AUTOMATION C] Proposal stage not found")
            return {"processed": 0, "skipped": 0, "error": "proposal_stage_not_found"}
        
        # Subquery: last activity per opportunity
        last_activity_subq = db.query(
            Activity.opportunity_id,
            func.max(Activity.occurred_at).label('last_activity')
        ).group_by(Activity.opportunity_id).subquery()
        
        # Opportunities in proposal stage with no recent activity
        opportunities = db.query(Opportunity).outerjoin(
            last_activity_subq,
            Opportunity.id == last_activity_subq.c.opportunity_id
        ).filter(
            Opportunity.stage_id == proposal_stage.id,
            Opportunity.status == 'active',
            Opportunity.close_outcome == 'open',
            func.coalesce(last_activity_subq.c.last_activity, datetime(1900, 1, 1, tzinfo=timezone.utc)) <= cutoff_date
        ).all()
        
        processed = 0
        skipped = 0
        
        for opp in opportunities:
            # Check dedupe: task "Seguimiento propuesta" open in last dedup_days
            existing_task = db.query(Task).filter(
                Task.opportunity_id == opp.id,
                Task.title == 'Seguimiento propuesta',
                Task.status == 'open',
                Task.created_at >= dedup_cutoff
            ).first()
            
            if existing_task:
                skipped += 1
                continue
            
            # Create task
            due_date = (today_dt + timedelta(days=2)).date()
            task = Task(
                id=generate_id(),
                opportunity_id=opp.id,
                task_template_id=None,
                title='Seguimiento propuesta',
                due_date=due_date,
                status='open',
                assigned_to_user_id=opp.owner_user_id,
                created_at=get_utc_now(),
                updated_at=get_utc_now()
            )
            db.add(task)
            
            # Create system activity
            activity = Activity(
                id=generate_id(),
                opportunity_id=opp.id,
                type='system',
                occurred_at=get_utc_now(),
                summary=f"Auto proposal follow-up created (no activity in {no_activity_days} days)",
                created_by_user_id=None,
                created_at=get_utc_now()
            )
            db.add(activity)
            
            # Audit log
            create_audit_log(
                db=db,
                entity="opportunities",
                entity_id=opp.id,
                action="auto_proposal_followup",
                user_id=None,
                after_data={
                    "opportunity_id": opp.id,
                    "task_id": task.id,
                    "no_activity_days": no_activity_days
                }
            )
            
            processed += 1
        
        db.commit()
        
        logger.info(f"[AUTOMATION C] Proposal follow-up: {processed} processed, {skipped} skipped (deduped)")
        return {"processed": processed, "skipped": skipped}
        
    except Exception as e:
        db.rollback()
        logger.error(f"[AUTOMATION C] Error: {e}")
        raise
    finally:
        db.close()


# ============================================================================
# RUN ALL AUTOMATIONS
# ============================================================================

def run_all_automations():
    """Run all 3 automations in sequence"""
    logger.info("=" * 70)
    logger.info("STARTING DAILY AUTOMATIONS")
    logger.info("=" * 70)
    
    results = {}
    
    try:
        # A) Overdue tasks
        results['overdue'] = automation_overdue_tasks()
        
        # B) No activity
        results['no_activity'] = automation_no_activity()
        
        # C) Proposal follow-up
        results['proposal_followup'] = automation_proposal_followup()
        
        logger.info("=" * 70)
        logger.info("AUTOMATIONS COMPLETED SUCCESSFULLY")
        logger.info(f"Results: {results}")
        logger.info("=" * 70)
        
        return results
        
    except Exception as e:
        logger.error(f"AUTOMATION FAILED: {e}")
        raise
