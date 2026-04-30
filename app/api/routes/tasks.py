"""
Tasks API endpoints
CRUD completo para gestión de tareas
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.database import get_db
from app.models.user import User
from app.models.opportunity import Task, Opportunity, Activity
from app.models.account import Account
from app.models.config import CfgTaskTemplate
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse, 
    TaskComplete, TaskWithRelations
)
from app.utils.auth import get_current_user_from_cookie, require_role
from app.utils.audit import create_audit_log, generate_id, get_iso_timestamp, get_utc_now, ENTITY_TASKS
from typing import Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse)
def list_tasks(
    assigned_to: Optional[str] = Query(None, description="Filter by assigned user ID"),
    status: Optional[List[str]] = Query(None, description="Filter by status (repeatable)"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    opportunity_id: Optional[str] = Query(None, description="Filter by opportunity"),
    account_id: Optional[str] = Query(None, description="Filter by account"),
    overdue: Optional[bool] = Query(None, description="Show only overdue tasks"),
    task_template_id: Optional[str] = Query(None, description="Filter by task template (type)"),
    limit: Optional[int] = Query(None, description="Max results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    List tasks with optional filters
    
    **Permissions:** All authenticated users
    - Admin: sees all tasks
    - Sales: sees all tasks
    - Viewer: sees only assigned tasks
    """
    query = db.query(Task)
    
    # Viewer and commercial can only see their own tasks
    if current_user.role in ('viewer', 'commercial'):
        query = query.filter(Task.assigned_to_user_id == current_user.id)
    
    # Apply filters
    if assigned_to:
        query = query.filter(Task.assigned_to_user_id == assigned_to)
    
    if status:
        if isinstance(status, list):
            query = query.filter(Task.status.in_(status))
        else:
            query = query.filter(Task.status == status)
    
    if priority:
        query = query.filter(Task.priority == priority)
    
    if opportunity_id:
        query = query.filter(Task.opportunity_id == opportunity_id)
    
    if account_id:
        query = query.filter(Task.account_id == account_id)
    
    # Filter overdue tasks
    if overdue:
        today = date.today()
        query = query.filter(
            and_(
                Task.due_date < today,
                Task.status.in_(['open', 'in_progress'])
            )
        )

    # 5E — Filtro por tipo de tarea
    if task_template_id:
        query = query.filter(Task.task_template_id == task_template_id)

    # Order by due_date (nulls last), then created_at
    q = query.order_by(
        Task.due_date.asc().nullslast(),
        Task.created_at.desc()
    )
    tasks = q.limit(limit).all() if limit else q.all()
    
    # Build response with relations
    tasks_with_relations = []
    for task in tasks:
        # Initialize all fields including names (important for Pydantic)
        task_dict = {
            "id": task.id,
            "opportunity_id": task.opportunity_id,
            "account_id": task.account_id,
            "task_template_id": task.task_template_id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date,
            "priority": task.priority,
            "status": task.status,
            "assigned_to_user_id": task.assigned_to_user_id,
            "completed_at": task.completed_at,
            "completed_by_user_id": task.completed_by_user_id,
            "reminder_date": task.reminder_date,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            # Initialize name fields as None
            "task_template_name": None,
            "opportunity_name": None,
            "account_name": None,
            "assigned_to_name": None,
            "completed_by_name": None
        }
        
        # Load task template name
        if task.task_template_id:
            template = db.query(CfgTaskTemplate).filter(CfgTaskTemplate.id == task.task_template_id).first()
            if template:
                task_dict["task_template_name"] = template.name
        
        # Load related entity names
        if task.opportunity_id:
            opp = db.query(Opportunity).filter(Opportunity.id == task.opportunity_id).first()
            if opp:
                task_dict["opportunity_name"] = opp.name or f"Oportunidad {opp.id[:8]}"
        
        if task.account_id:
            account = db.query(Account).filter(Account.id == task.account_id).first()
            if account:
                task_dict["account_name"] = account.name
        
        if task.assigned_to_user_id:
            user = db.query(User).filter(User.id == task.assigned_to_user_id).first()
            if user:
                task_dict["assigned_to_name"] = user.name
        
        if task.completed_by_user_id:
            user = db.query(User).filter(User.id == task.completed_by_user_id).first()
            if user:
                task_dict["completed_by_name"] = user.name
        
        tasks_with_relations.append(TaskWithRelations(**task_dict))
    
    return TaskListResponse(
        tasks=tasks_with_relations,
        total=len(tasks_with_relations)
    )


@router.get("/{task_id}", response_model=TaskWithRelations)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get a single task by ID
    
    **Permissions:** All authenticated users
    - Viewer: can only see assigned tasks
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Viewer can only see their own tasks
    if current_user.role == 'viewer' and task.assigned_to_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this task"
        )
    
    # Build response with relations
    task_dict = {
        "id": task.id,
        "opportunity_id": task.opportunity_id,
        "account_id": task.account_id,
        "task_template_id": task.task_template_id,
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date,
        "priority": task.priority,
        "status": task.status,
        "assigned_to_user_id": task.assigned_to_user_id,
        "completed_at": task.completed_at,
        "completed_by_user_id": task.completed_by_user_id,
        "reminder_date": task.reminder_date,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        # Initialize name fields as None
        "opportunity_name": None,
        "account_name": None,
        "assigned_to_name": None,
        "completed_by_name": None
    }
    
    # Load related entity names
    if task.opportunity_id:
        opp = db.query(Opportunity).filter(Opportunity.id == task.opportunity_id).first()
        if opp:
            task_dict["opportunity_name"] = opp.name or f"Oportunidad {opp.id[:8]}"
    
    if task.account_id:
        account = db.query(Account).filter(Account.id == task.account_id).first()
        if account:
            task_dict["account_name"] = account.name
    
    if task.assigned_to_user_id:
        user = db.query(User).filter(User.id == task.assigned_to_user_id).first()
        if user:
            task_dict["assigned_to_name"] = user.name
    
    if task.completed_by_user_id:
        user = db.query(User).filter(User.id == task.completed_by_user_id).first()
        if user:
            task_dict["completed_by_name"] = user.name
    
    return TaskWithRelations(**task_dict)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales", "commercial"))
):
    """
    Create a new task

    **Permissions:** Admin, Sales and Commercial
    
    **Validation:**
    - At least one of opportunity_id or account_id must be provided
    - If opportunity_id provided, must exist
    - If account_id provided, must exist
    """
    # Validate: at least one link must be present
    if not task_data.opportunity_id and not task_data.account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task must be linked to either an opportunity or an account"
        )
    
    # Validate opportunity exists
    if task_data.opportunity_id:
        opp = db.query(Opportunity).filter(Opportunity.id == task_data.opportunity_id).first()
        if not opp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Opportunity {task_data.opportunity_id} not found"
            )
    
    # Validate account exists
    if task_data.account_id:
        account = db.query(Account).filter(Account.id == task_data.account_id).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account {task_data.account_id} not found"
            )
    
    # Create task
    timestamp = get_utc_now()
    new_task = Task(
        id=generate_id(),
        opportunity_id=task_data.opportunity_id,
        account_id=task_data.account_id,
        task_template_id=task_data.task_template_id,
        title=task_data.title,
        description=task_data.description,
        due_date=task_data.due_date,
        priority=task_data.priority,
        status='open',
        assigned_to_user_id=task_data.assigned_to_user_id,
        created_by_user_id=current_user.id,
        reminder_date=task_data.reminder_date,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    db.add(new_task)
    
    # Create audit log
    create_audit_log(
        db=db,
        entity=ENTITY_TASKS,
        entity_id=new_task.id,
        action="create",
        user_id=current_user.id,
        after_data={
            "title": new_task.title,
            "opportunity_id": new_task.opportunity_id,
            "account_id": new_task.account_id,
            "priority": new_task.priority,
            "due_date": new_task.due_date,
            "assigned_to": new_task.assigned_to_user_id
        }
    )
    
    # Create activity if linked to opportunity
    if task_data.opportunity_id:
        from app.api.routes.activities import create_activity_auto
        
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        emoji = priority_emoji.get(task_data.priority, "⚪")
        
        create_activity_auto(
            db=db,
            opportunity_id=task_data.opportunity_id,
            activity_type="task_created",
            summary=f"Nueva tarea creada: {emoji} {task_data.title}",
            user_id=current_user.id
        )
    
    db.commit()
    db.refresh(new_task)
    
    logger.info(f"Task created: {new_task.id} by {current_user.email}")
    
    return TaskResponse(
        id=new_task.id,
        opportunity_id=new_task.opportunity_id,
        account_id=new_task.account_id,
        task_template_id=new_task.task_template_id,
        title=new_task.title,
        description=new_task.description,
        due_date=new_task.due_date,
        priority=new_task.priority,
        status=new_task.status,
        assigned_to_user_id=new_task.assigned_to_user_id,
        completed_at=new_task.completed_at,
        completed_by_user_id=new_task.completed_by_user_id,
        reminder_date=new_task.reminder_date,
        created_at=new_task.created_at,
        updated_at=new_task.updated_at
    )


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales", "commercial"))
):
    """
    Update a task

    **Permissions:** Admin, Sales and Commercial (own tasks only)
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if current_user.role == "commercial":
        if (task.assigned_to_user_id != current_user.id and
                task.created_by_user_id != current_user.id):
            raise HTTPException(status_code=403,
                detail="Solo puedes editar tus propias tareas")

    # Store before state
    before_data = {
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": task.status,
        "due_date": task.due_date,
        "assigned_to": task.assigned_to_user_id
    }
    
    # Apply all explicitly-provided fields, including null values (allows clearing
    # opportunity_id / account_id / description / etc. by sending null in payload)
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    # Validate: at least one link must remain
    if not task.opportunity_id and not task.account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task must be linked to either an opportunity or an account"
        )
    
    task.updated_at = get_utc_now()
    
    # Store after state
    after_data = {
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": task.status,
        "due_date": task.due_date,
        "assigned_to": task.assigned_to_user_id
    }
    
    # Create audit log
    create_audit_log(
        db=db,
        entity=ENTITY_TASKS,
        entity_id=task.id,
        action="update",
        user_id=current_user.id,
        before_data=before_data,
        after_data=after_data
    )
    
    db.commit()
    db.refresh(task)
    
    logger.info(f"Task updated: {task.id} by {current_user.email}")
    
    return TaskResponse(
        id=task.id,
        opportunity_id=task.opportunity_id,
        account_id=task.account_id,
        task_template_id=task.task_template_id,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        priority=task.priority,
        status=task.status,
        assigned_to_user_id=task.assigned_to_user_id,
        completed_at=task.completed_at,
        completed_by_user_id=task.completed_by_user_id,
        reminder_date=task.reminder_date,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.delete("/{task_id}", response_model=dict)
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales", "commercial"))
):
    """
    Delete (cancel) a task

    **Permissions:** Admin, Sales and Commercial (own tasks only)

    **Note:** This is a logical delete - task status is set to 'cancelled'
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if current_user.role == "commercial":
        if (task.assigned_to_user_id != current_user.id and
                task.created_by_user_id != current_user.id):
            raise HTTPException(status_code=403,
                detail="Solo puedes editar tus propias tareas")

    # Logical delete: set status to cancelled
    task.status = 'cancelled'
    task.updated_at = get_utc_now()
    
    # Create audit log
    create_audit_log(
        db=db,
        entity=ENTITY_TASKS,
        entity_id=task.id,
        action="delete",
        user_id=current_user.id,
        after_data={
            "status": "cancelled",
            "cancelled_by": current_user.email
        }
    )
    
    db.commit()
    
    logger.info(f"Task cancelled: {task.id} by {current_user.email}")
    
    return {
        "message": "Task cancelled successfully",
        "task_id": task.id
    }


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Mark a task as completed
    
    **Permissions:** All authenticated users (can complete their own tasks)
    - Admin/Sales: can complete any task
    - Viewer: can only complete assigned tasks
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Viewer can only complete their own tasks
    if current_user.role == 'viewer' and task.assigned_to_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to complete this task"
        )
    
    # Update task
    task.status = 'completed'
    task.completed_at = get_utc_now()
    task.completed_by_user_id = current_user.id
    task.updated_at = get_utc_now()
    
    # Create audit log
    create_audit_log(
        db=db,
        entity=ENTITY_TASKS,
        entity_id=task.id,
        action="complete",
        user_id=current_user.id,
        after_data={
            "status": "completed",
            "completed_by": current_user.email,
            "completed_at": task.completed_at
        }
    )
    
    # Create activity if linked to opportunity
    if task.opportunity_id:
        activity = Activity(
            id=generate_id(),
            opportunity_id=task.opportunity_id,
            type="task_completed",
            occurred_at=task.completed_at,
            summary=f"Tarea completada: {task.title}",
            created_by_user_id=current_user.id,
            created_at=get_utc_now()
        )
        db.add(activity)
    
    db.commit()
    db.refresh(task)
    
    logger.info(f"Task completed: {task.id} by {current_user.email}")
    
    return TaskResponse(
        id=task.id,
        opportunity_id=task.opportunity_id,
        account_id=task.account_id,
        task_template_id=task.task_template_id,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        priority=task.priority,
        status=task.status,
        assigned_to_user_id=task.assigned_to_user_id,
        completed_at=task.completed_at,
        completed_by_user_id=task.completed_by_user_id,
        reminder_date=task.reminder_date,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.post("/{task_id}/reopen", response_model=TaskResponse)
def reopen_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Reopen a completed task
    
    **Permissions:** Admin and Sales only
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Update task
    task.status = 'open'
    task.completed_at = None
    task.completed_by_user_id = None
    task.updated_at = get_utc_now()
    
    # Create audit log
    create_audit_log(
        db=db,
        entity=ENTITY_TASKS,
        entity_id=task.id,
        action="reopen",
        user_id=current_user.id,
        after_data={
            "status": "open",
            "reopened_by": current_user.email
        }
    )
    
    db.commit()
    db.refresh(task)
    
    logger.info(f"Task reopened: {task.id} by {current_user.email}")
    
    return TaskResponse(
        id=task.id,
        opportunity_id=task.opportunity_id,
        account_id=task.account_id,
        task_template_id=task.task_template_id,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        priority=task.priority,
        status=task.status,
        assigned_to_user_id=task.assigned_to_user_id,
        completed_at=task.completed_at,
        completed_by_user_id=task.completed_by_user_id,
        reminder_date=task.reminder_date,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.get("/opportunity/{opportunity_id}", response_model=TaskListResponse)
def get_opportunity_tasks(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get all tasks for a specific opportunity
    
    **Permissions:** All authenticated users
    """
    # Verify opportunity exists
    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    # Get tasks (excluir canceladas — son soft-deletes)
    tasks = db.query(Task).filter(
        Task.opportunity_id == opportunity_id,
        Task.status != 'cancelled'
    ).order_by(
        Task.due_date.asc().nullslast(),
        Task.created_at.desc()
    ).all()
    
    # Build responses with relations
    tasks_with_relations = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "opportunity_id": task.opportunity_id,
            "account_id": task.account_id,
            "task_template_id": task.task_template_id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date,
            "priority": task.priority,
            "status": task.status,
            "assigned_to_user_id": task.assigned_to_user_id,
            "completed_at": task.completed_at,
            "completed_by_user_id": task.completed_by_user_id,
            "reminder_date": task.reminder_date,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "opportunity_name": opp.name or f"Oportunidad {opp.id[:8]}",
            "account_name": None,
            "assigned_to_name": None,
            "completed_by_name": None
        }
        
        if task.assigned_to_user_id:
            user = db.query(User).filter(User.id == task.assigned_to_user_id).first()
            if user:
                task_dict["assigned_to_name"] = user.name
        
        tasks_with_relations.append(TaskWithRelations(**task_dict))
    
    return TaskListResponse(
        tasks=tasks_with_relations,
        total=len(tasks_with_relations)
    )


@router.get("/account/{account_id}", response_model=TaskListResponse)
def get_account_tasks(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get all tasks for a specific account
    
    Includes:
    - Tasks directly linked to the account
    - Tasks linked to opportunities of this account
    
    **Permissions:** All authenticated users
    """
    # Verify account exists
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Get direct tasks
    direct_tasks = db.query(Task).filter(Task.account_id == account_id).all()
    
    # Get tasks from opportunities
    opportunities = db.query(Opportunity).filter(Opportunity.account_id == account_id).all()
    opp_ids = [opp.id for opp in opportunities]
    
    opp_tasks = []
    if opp_ids:
        opp_tasks = db.query(Task).filter(Task.opportunity_id.in_(opp_ids)).all()
    
    # Combine and deduplicate
    all_tasks = list({task.id: task for task in direct_tasks + opp_tasks}.values())
    
    # Sort
    all_tasks.sort(key=lambda t: (t.due_date or '9999-99-99', t.created_at), reverse=False)
    
    # Build responses with relations
    tasks_with_relations = []
    for task in all_tasks:
        task_dict = {
            "id": task.id,
            "opportunity_id": task.opportunity_id,
            "account_id": task.account_id,
            "task_template_id": task.task_template_id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date,
            "priority": task.priority,
            "status": task.status,
            "assigned_to_user_id": task.assigned_to_user_id,
            "completed_at": task.completed_at,
            "completed_by_user_id": task.completed_by_user_id,
            "reminder_date": task.reminder_date,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "account_name": account.name,
            "opportunity_name": None,
            "assigned_to_name": None,
            "completed_by_name": None
        }
        
        if task.opportunity_id:
            opp = db.query(Opportunity).filter(Opportunity.id == task.opportunity_id).first()
            if opp:
                task_dict["opportunity_name"] = opp.name or f"Oportunidad {opp.id[:8]}"
        
        if task.assigned_to_user_id:
            user = db.query(User).filter(User.id == task.assigned_to_user_id).first()
            if user:
                task_dict["assigned_to_name"] = user.name
        
        tasks_with_relations.append(TaskWithRelations(**task_dict))
    
    return TaskListResponse(
        tasks=tasks_with_relations,
        total=len(tasks_with_relations)
    )


@router.get("/account/{account_id}", response_model=TaskListResponse)
async def get_account_tasks(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_cookie)
):
    """
    Get all tasks for an account (direct + from opportunities)
    """
    logger.info(f"Getting tasks for account {account_id}")
    
    # Get direct tasks for account
    direct_tasks = db.query(Task).filter(
        Task.account_id == account_id,
        Task.status != 'cancelled'
    ).all()
    
    # Get tasks from opportunities of this account
    account_opportunities = db.query(Opportunity).filter(
        Opportunity.account_id == account_id
    ).all()
    
    opp_ids = [opp.id for opp in account_opportunities]
    opp_tasks = []
    if opp_ids:
        opp_tasks = db.query(Task).filter(
            Task.opportunity_id.in_(opp_ids),
            Task.status != 'cancelled'
        ).all()
    
    # Combine and deduplicate
    all_tasks = list({task.id: task for task in direct_tasks + opp_tasks}.values())
    
    # Sort by due date
    all_tasks.sort(key=lambda t: t.due_date or '9999-12-31')
    
    # Build response with relations
    tasks_with_relations = []
    for task in all_tasks:
        task_dict = {
            "id": task.id,
            "opportunity_id": task.opportunity_id,
            "account_id": task.account_id,
            "task_template_id": task.task_template_id,
            "title": task.title,
            "description": task.description,
            "due_date": task.due_date,
            "priority": task.priority,
            "status": task.status,
            "assigned_to_user_id": task.assigned_to_user_id,
            "completed_at": task.completed_at,
            "completed_by_user_id": task.completed_by_user_id,
            "reminder_date": task.reminder_date,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "task_template_name": None,
            "opportunity_name": None,
            "account_name": None,
            "assigned_to_name": None,
            "completed_by_name": None
        }
        
        # Load template name
        if task.task_template_id:
            template = db.query(CfgTaskTemplate).filter(CfgTaskTemplate.id == task.task_template_id).first()
            if template:
                task_dict["task_template_name"] = template.name
        
        # Load opportunity name
        if task.opportunity_id:
            opp = db.query(Opportunity).filter(Opportunity.id == task.opportunity_id).first()
            if opp:
                task_dict["opportunity_name"] = opp.name or f"Oportunidad {opp.id[:8]}"
        
        # Load account name
        if task.account_id:
            account = db.query(Account).filter(Account.id == task.account_id).first()
            if account:
                task_dict["account_name"] = account.name
        
        # Load assigned user
        if task.assigned_to_user_id:
            user = db.query(User).filter(User.id == task.assigned_to_user_id).first()
            if user:
                task_dict["assigned_to_name"] = user.name
        
        # Load completed by user
        if task.completed_by_user_id:
            user = db.query(User).filter(User.id == task.completed_by_user_id).first()
            if user:
                task_dict["completed_by_name"] = user.name
        
        tasks_with_relations.append(TaskWithRelations(**task_dict))
    
    return TaskListResponse(
        tasks=tasks_with_relations,
        total=len(tasks_with_relations)
    )
