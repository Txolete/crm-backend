"""
Endpoints for user feedback (in-app feedback widget)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.feedback import UserFeedback
from app.schemas.feedback import (
    FeedbackCreate, FeedbackResponse, FeedbackListResponse, FeedbackUpdate
)
from app.utils.auth import get_current_user_from_cookie
from app.utils.audit import generate_id, get_utc_now
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """
    Cualquier usuario autenticado puede enviar feedback desde el widget.
    """
    fb = UserFeedback(
        id=generate_id(),
        user_id=current_user.id,
        message=payload.message.strip(),
        view=payload.view,
        url=payload.url,
        user_agent=(request.headers.get("user-agent") or "")[:500],
        status="open",
        created_at=get_utc_now(),
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    logger.info(f"[feedback] new feedback from user={current_user.id} view={payload.view}")
    return FeedbackResponse(
        id=fb.id,
        user_id=fb.user_id,
        user_name=current_user.name,
        message=fb.message,
        view=fb.view,
        url=fb.url,
        user_agent=fb.user_agent,
        status=fb.status,
        created_at=fb.created_at,
    )


@router.get("", response_model=FeedbackListResponse)
def list_feedback(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(200, le=500),
):
    """
    Lista de feedback. Solo admin ve todo; otros usuarios solo el suyo.
    """
    q = db.query(UserFeedback)
    if current_user.role != "admin":
        q = q.filter(UserFeedback.user_id == current_user.id)
    if status_filter:
        q = q.filter(UserFeedback.status == status_filter)
    items = q.order_by(desc(UserFeedback.created_at)).limit(limit).all()

    user_ids = {i.user_id for i in items if i.user_id}
    users = {u.id: u.name for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}

    return FeedbackListResponse(
        feedback=[
            FeedbackResponse(
                id=i.id,
                user_id=i.user_id,
                user_name=users.get(i.user_id),
                message=i.message,
                view=i.view,
                url=i.url,
                user_agent=i.user_agent,
                status=i.status,
                created_at=i.created_at,
                reviewed_at=i.reviewed_at,
                reviewed_by_user_id=i.reviewed_by_user_id,
                admin_note=i.admin_note,
            )
            for i in items
        ],
        total=len(items),
    )


@router.patch("/{feedback_id}", response_model=FeedbackResponse)
def update_feedback(
    feedback_id: str,
    payload: FeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """
    Solo admin puede cambiar status / nota.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin puede actualizar feedback")
    fb = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback no encontrado")
    if payload.status is not None:
        fb.status = payload.status
        fb.reviewed_at = get_utc_now()
        fb.reviewed_by_user_id = current_user.id
    if payload.admin_note is not None:
        fb.admin_note = payload.admin_note
    db.commit()
    db.refresh(fb)
    user_name = db.query(User.name).filter(User.id == fb.user_id).scalar() if fb.user_id else None
    return FeedbackResponse(
        id=fb.id,
        user_id=fb.user_id,
        user_name=user_name,
        message=fb.message,
        view=fb.view,
        url=fb.url,
        user_agent=fb.user_agent,
        status=fb.status,
        created_at=fb.created_at,
        reviewed_at=fb.reviewed_at,
        reviewed_by_user_id=fb.reviewed_by_user_id,
        admin_note=fb.admin_note,
    )
