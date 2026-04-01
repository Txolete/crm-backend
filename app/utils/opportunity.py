"""
Opportunity utilities and helpers
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional
from app.models.opportunity import Task

# ---------------------------------------------------------------------------
# Probability / weighted-value helpers  (canonical, single source of truth)
# ---------------------------------------------------------------------------

DEFAULT_STAGE_PROBABILITIES = {
    "new": 0.05,
    "contacted": 0.10,
    "qualified": 0.30,
    "proposal": 0.50,
    "negotiation": 0.70,
    "won": 1.00,
    "lost": 0.00,
}


def calculate_probability(opportunity, stage_probs_map: dict, stages_map: dict) -> float:
    """
    Calculate probability for an opportunity.

    Priority:
    1. probability_override on the opportunity itself
    2. Configured probability from cfg_stage_probabilities (stage_probs_map)
    3. Hard-coded defaults by stage key
    4. Fallback 0.0
    """
    if opportunity.probability_override is not None:
        return opportunity.probability_override

    if opportunity.stage_id in stage_probs_map:
        return stage_probs_map[opportunity.stage_id]

    stage = stages_map.get(opportunity.stage_id)
    if stage and stage.key in DEFAULT_STAGE_PROBABILITIES:
        return DEFAULT_STAGE_PROBABILITIES[stage.key]

    return 0.0


def calculate_weighted_value(opportunity, probability: float) -> float:
    """
    Calculate weighted value for an opportunity.

    If weighted_value_override_eur is set, return that directly.
    Otherwise: expected_value_eur * probability.
    """
    if opportunity.weighted_value_override_eur is not None:
        return opportunity.weighted_value_override_eur
    return opportunity.expected_value_eur * probability


def get_next_open_task(db: Session, opportunity_id: str) -> Optional[Task]:
    """
    Get the next open task for an opportunity
    
    Rules:
    - Only tasks with status='open'
    - Ordered by due_date ascending (nulls last)
    - Returns Task object or None
    
    Args:
        db: Database session
        opportunity_id: ID of the opportunity
        
    Returns:
        Task object or None if no open tasks
    """
    # Query open tasks for this opportunity
    open_tasks = db.query(Task).filter(
        and_(
            Task.opportunity_id == opportunity_id,
            Task.status == "open"
        )
    ).all()
    
    if not open_tasks:
        return None
    
    # Sort: tasks with due_date first (ascending), then tasks without due_date
    # NULLS LAST implementation for SQLite compatibility
    def sort_key(task):
        if task.due_date is None:
            # Put tasks without due_date at the end (NULLS LAST)
            return (1, "9999-12-31")
        else:
            # Tasks with due_date come first, sorted by date ascending
            return (0, task.due_date)
    
    sorted_tasks = sorted(open_tasks, key=sort_key)
    
    return sorted_tasks[0] if sorted_tasks else None


def get_task_stats(db: Session, opportunity_id: str) -> dict:
    """
    Get task statistics for an opportunity
    
    Returns:
        dict with:
        - open_tasks_count: Number of open tasks
        - done_tasks_count: Number of completed tasks
    
    Args:
        db: Database session
        opportunity_id: ID of the opportunity
        
    Returns:
        dict with task counts
    """
    # Count open tasks
    open_count = db.query(func.count(Task.id)).filter(
        and_(
            Task.opportunity_id == opportunity_id,
            Task.status == "open"
        )
    ).scalar() or 0
    
    # Count completed tasks
    done_count = db.query(func.count(Task.id)).filter(
        and_(
            Task.opportunity_id == opportunity_id,
            Task.status == "done"
        )
    ).scalar() or 0
    
    return {
        "open_tasks_count": open_count,
        "done_tasks_count": done_count
    }


def get_opportunity_summary(db: Session, opportunity_id: str) -> dict:
    """
    Get a complete summary of an opportunity for display in Kanban/Dashboard
    
    Combines get_next_open_task and get_task_stats for convenience
    
    Returns:
        dict with:
        - next_task: Next open task details (title + due_date) or None
        - open_tasks_count: Number of open tasks
        - completed_tasks_count: Number of completed tasks
        
    Args:
        db: Database session
        opportunity_id: ID of the opportunity
        
    Returns:
        dict with opportunity summary
    """
    # Get next open task
    next_task = get_next_open_task(db, opportunity_id)
    
    # Get task stats
    stats = get_task_stats(db, opportunity_id)
    
    return {
        "next_task": {
            "title": next_task.title if next_task else None,
            "due_date": next_task.due_date if next_task else None
        } if next_task else None,
        "open_tasks_count": stats["open_tasks_count"],
        "done_tasks_count": stats["done_tasks_count"]
    }
