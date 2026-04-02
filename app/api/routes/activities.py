"""
Activity API routes - Timeline functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.opportunity import Opportunity, Activity
from app.schemas.activity import (
    ActivityCreate, ActivityUpdate, ActivityResponse, ActivityListResponse
)
from app.utils.auth import get_current_user_from_cookie, require_role
from app.utils.audit import generate_id, get_iso_timestamp, get_utc_now
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/activities", tags=["Activities"])


# ============================================================================
# CRUD ENDPOINTS
# ============================================================================

@router.get("/opportunity/{opportunity_id}", response_model=ActivityListResponse)
async def list_activities_by_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get all activities for an opportunity (timeline)
    
    **Permissions:** All authenticated users
    """
    # Verify opportunity exists
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Oportunidad no encontrada"
        )
    
    # Get activities ordered by occurred_at DESC (most recent first)
    activities = db.query(Activity).filter(
        Activity.opportunity_id == opportunity_id
    ).order_by(Activity.occurred_at.desc()).all()
    
    # Build response with user names
    activities_with_names = []
    for activity in activities:
        activity_dict = {
            "id": activity.id,
            "opportunity_id": activity.opportunity_id,
            "type": activity.type,
            "occurred_at": activity.occurred_at,
            "summary": activity.summary,
            "created_by_user_id": activity.created_by_user_id,
            "created_by_name": None,
            "created_at": activity.created_at
        }
        
        # Load creator name
        if activity.created_by_user_id:
            user = db.query(User).filter(User.id == activity.created_by_user_id).first()
            if user:
                activity_dict["created_by_name"] = user.name
        
        activities_with_names.append(ActivityResponse(**activity_dict))
    
    return ActivityListResponse(
        activities=activities_with_names,
        total=len(activities_with_names)
    )


@router.post("", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    activity_data: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Create a new activity (manual entry)
    
    **Permissions:** admin, sales
    """
    timestamp = get_utc_now()
    
    # Verify opportunity exists
    opportunity = db.query(Opportunity).filter(
        Opportunity.id == activity_data.opportunity_id
    ).first()
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Oportunidad no encontrada"
        )
    
    # Create activity
    new_activity = Activity(
        id=generate_id(),
        opportunity_id=activity_data.opportunity_id,
        type=activity_data.type,
        occurred_at=activity_data.occurred_at or timestamp,  # Default to now
        summary=activity_data.summary,
        created_by_user_id=current_user.id,
        created_at=timestamp
    )
    
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    
    logger.info(f"Activity created: {new_activity.id} for opportunity {activity_data.opportunity_id}")
    
    # Return with user name
    return ActivityResponse(
        id=new_activity.id,
        opportunity_id=new_activity.opportunity_id,
        type=new_activity.type,
        occurred_at=new_activity.occurred_at,
        summary=new_activity.summary,
        created_by_user_id=new_activity.created_by_user_id,
        created_by_name=current_user.name,
        created_at=new_activity.created_at
    )


@router.put("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: str,
    activity_data: ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Update an existing activity
    
    **Permissions:** admin, sales (only own activities)
    """
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad no encontrada"
        )
    
    # Only admin or creator can edit
    if current_user.role != "admin" and activity.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para editar esta actividad"
        )
    
    # Update fields
    if activity_data.summary is not None:
        activity.summary = activity_data.summary
    if activity_data.occurred_at is not None:
        activity.occurred_at = activity_data.occurred_at
    
    db.commit()
    db.refresh(activity)
    
    logger.info(f"Activity updated: {activity_id}")
    
    # Return with user name
    creator_name = None
    if activity.created_by_user_id:
        user = db.query(User).filter(User.id == activity.created_by_user_id).first()
        if user:
            creator_name = user.name
    
    return ActivityResponse(
        id=activity.id,
        opportunity_id=activity.opportunity_id,
        type=activity.type,
        occurred_at=activity.occurred_at,
        summary=activity.summary,
        created_by_user_id=activity.created_by_user_id,
        created_by_name=creator_name,
        created_at=activity.created_at
    )


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Delete an activity
    
    **Permissions:** admin, sales (only own activities)
    """
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad no encontrada"
        )
    
    # Only admin or creator can delete
    if current_user.role != "admin" and activity.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar esta actividad"
        )
    
    db.delete(activity)
    db.commit()
    
    logger.info(f"Activity deleted: {activity_id}")
    return


# ============================================================================
# HELPER FUNCTIONS FOR AUTO-CREATION
# ============================================================================

def create_activity_auto(
    db: Session,
    opportunity_id: str,
    activity_type: str,
    summary: str,
    user_id: Optional[str] = None
) -> Activity:
    """
    Helper function to create activities automatically
    
    Used by:
    - Opportunity status changes
    - Task creation/completion
    - Won/Lost events
    
    NOTE: Does NOT commit - calling function must commit
    """
    timestamp = get_utc_now()
    
    new_activity = Activity(
        id=generate_id(),
        opportunity_id=opportunity_id,
        type=activity_type,
        occurred_at=timestamp,
        summary=summary,
        created_by_user_id=user_id,
        created_at=timestamp
    )
    
    db.add(new_activity)
    
    logger.info(f"Auto-activity created: {activity_type} for opportunity {opportunity_id}")
    return new_activity
