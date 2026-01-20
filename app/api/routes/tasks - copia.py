"""
Task endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date
from app.database import get_db
from app.models.user import User
from app.models.opportunity import Task
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
)
from app.utils.auth import get_current_user_from_cookie, require_role
from app.utils.audit import create_audit_log, generate_id, get_iso_timestamp, ENTITY_TASKS
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse)
def list_tasks(
    mode: Optional[str] = Query(None, pattern="^(today|overdue|open|done|all)$"),
    assigned_to_user_id: Optional[str] = Query(None),
    opportunity_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    List tasks with filters
    
    **Permissions:** All authenticated users
    
    **Mode filters:**
    - today: due_date = today AND status = 'open'
    - overdue: due_date < today AND status = 'open'
    - open: status = 'open'
    - done: status = 'done'
    - all: no filter
    """
    query = db.query(Task)
    
    today = date.today().isoformat()
    
    # Filter by mode
    if mode == "today":
        query = query.filter(Task.due_date == today, Task.status == "open")
    elif mode == "overdue":
        query = query.filter(Task.due_date < today, Task.status == "open")
    elif mode == "open":
        query = query.filter(Task.status == "open")
    elif mode == "done":
        query = query.filter(Task.status == "done")
    # 'all' or None = no status filter
    
    # Filter by assigned user
    if assigned_to_user_id:
        query = query.filter(Task.assigned_to_user_id == assigned_to_user_id)
    
    # Filter by opportunity
    if opportunity_id:
        query = query.filter(Task.opportunity_id == opportunity_id)
    
    tasks = query.all()
    
    return TaskListResponse(
        tasks=[TaskResponse.model_validate(task) for task in tasks],
        total=len(tasks)
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Create a new task
    
    **Permissions:** admin, sales
    """
    timestamp = get_iso_timestamp()
    
    new_task = Task(
        id=generate_id(),
        opportunity_id=task_data.opportunity_id,
        task_template_id=task_data.task_template_id,
        title=task_data.title,
        due_date=task_data.due_date,
        status="open",  # Always starts as open
        assigned_to_user_id=task_data.assigned_to_user_id,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    db.add(new_task)
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_TASKS,
        entity_id=new_task.id,
        action="create",
        user_id=current_user.id,
        after_data={
            "opportunity_id": new_task.opportunity_id,
            "title": new_task.title,
            "due_date": new_task.due_date,
            "status": new_task.status,
            "assigned_to_user_id": new_task.assigned_to_user_id
        }
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(new_task)
    
    logger.info(f"Task created: {new_task.id} by {current_user.email}")
    
    return TaskResponse.model_validate(new_task)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get task by ID
    
    **Permissions:** All authenticated users
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return TaskResponse.model_validate(task)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Update task
    
    **Permissions:** admin, sales
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Store before state
    before_data = {
        "title": task.title,
        "due_date": task.due_date,
        "status": task.status,
        "assigned_to_user_id": task.assigned_to_user_id
    }
    
    # Update fields
    if task_data.task_template_id is not None:
        task.task_template_id = task_data.task_template_id
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.due_date is not None:
        task.due_date = task_data.due_date
    if task_data.status is not None:
        task.status = task_data.status
    if task_data.assigned_to_user_id is not None:
        task.assigned_to_user_id = task_data.assigned_to_user_id
    
    task.updated_at = get_iso_timestamp()
    
    # Store after state
    after_data = {
        "title": task.title,
        "due_date": task.due_date,
        "status": task.status,
        "assigned_to_user_id": task.assigned_to_user_id
    }
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_TASKS,
        entity_id=task.id,
        action="update",
        user_id=current_user.id,
        before_data=before_data,
        after_data=after_data
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(task)
    
    logger.info(f"Task updated: {task.id} by {current_user.email}")
    
    return TaskResponse.model_validate(task)


@router.post("/{task_id}/cancel", response_model=TaskResponse)
def cancel_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Cancel task (set status to 'canceled')
    
    **Permissions:** admin, sales
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status == "canceled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task already canceled"
        )
    
    # Store before state
    before_data = {
        "status": task.status
    }
    
    task.status = "canceled"
    task.updated_at = get_iso_timestamp()
    
    # Store after state
    after_data = {
        "status": task.status
    }
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_TASKS,
        entity_id=task.id,
        action="cancel",
        user_id=current_user.id,
        before_data=before_data,
        after_data=after_data
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(task)
    
    logger.info(f"Task canceled: {task.id} by {current_user.email}")
    
    return TaskResponse.model_validate(task)


# PASO 8 - Tasks Overview (Semáforo)
from datetime import timedelta
from app.models.opportunity import Opportunity
from app.models.account import Account
from app.models.config import CfgStage
from app.schemas.tasks import TasksOverviewResponse, TaskOverviewItem

@router.get("/overview", response_model=TasksOverviewResponse)
def tasks_overview(
    assigned_to: str = Query("me", pattern="^(me|all)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get tasks overview (semáforo)
    
    PASO 8 - Returns tasks grouped by urgency:
    - overdue: due_date < today (RED)
    - due_soon: due_date in next 0-2 days (YELLOW)
    - upcoming: due_date in next 3-10 days (GREEN)
    
    Query params:
    - assigned_to: 'me' (current user) or 'all' (admin only)
    """
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    ten_days = today + timedelta(days=10)
    
    # Base query
    base_query = db.query(Task, Opportunity, Account, CfgStage).join(
        Opportunity, Task.opportunity_id == Opportunity.id
    ).join(
        Account, Opportunity.account_id == Account.id
    ).join(
        CfgStage, Opportunity.stage_id == CfgStage.id
    ).filter(
        Task.status == 'open',
        Task.due_date.isnot(None)
    )
    
    # Filter by assigned user
    if assigned_to == 'me':
        base_query = base_query.filter(Task.assigned_to_user_id == current_user.id)
    elif assigned_to == 'all':
        # Only admin can see all
        if current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin can view all tasks"
            )
    
    # Query overdue (RED)
    overdue_data = base_query.filter(
        Task.due_date < today.isoformat()
    ).all()
    
    # Query due soon (YELLOW) - today + next 2 days
    due_soon_data = base_query.filter(
        Task.due_date >= today.isoformat(),
        Task.due_date <= day_after.isoformat()
    ).all()
    
    # Query upcoming (GREEN) - next 3-10 days
    upcoming_data = base_query.filter(
        Task.due_date > day_after.isoformat(),
        Task.due_date <= ten_days.isoformat()
    ).all()
    
    # Format results
    def format_tasks(data):
        return [
            TaskOverviewItem(
                task_id=task.id,
                title=task.title,
                due_date=task.due_date,
                opportunity_id=opp.id,
                account_name=account.name,
                stage_key=stage.key,
                stage_name=stage.name
            )
            for task, opp, account, stage in data
        ]
    
    overdue = format_tasks(overdue_data)
    due_soon = format_tasks(due_soon_data)
    upcoming = format_tasks(upcoming_data)
    
    return TasksOverviewResponse(
        overdue=overdue,
        due_soon=due_soon,
        upcoming=upcoming,
        total_overdue=len(overdue),
        total_due_soon=len(due_soon),
        total_upcoming=len(upcoming)
    )
