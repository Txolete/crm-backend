"""
Admin endpoints for user management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse, UserResetPassword
)
from app.utils.security import hash_password
from app.utils.auth import require_role, get_current_user_from_cookie
from app.utils.audit import create_audit_log, generate_id, get_iso_timestamp, ENTITY_USERS
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin - User Management"])

# Configure Jinja2 templates
templates = Jinja2Templates(directory="app/templates")


@router.get("/users-page", response_class=HTMLResponse)
async def users_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Serve users management page
    
    **Permissions:** Admin only
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access user management"
        )
    
    return templates.TemplateResponse(
        "users.html",
        {"request": request}
    )


@router.get("/users", response_model=UserListResponse)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))  # admin y sales pueden listar
):
    """
    List all users
    
    **Admin and Sales** can list users (needed for owner assignment)
    
    Returns all users with their information (except password_hash)
    """
    users = db.query(User).all()
    
    return UserListResponse(
        users=[
            UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role,
                is_active=user.is_active == 1,  # Convert INTEGER to bool
                last_login_at=user.last_login_at,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ],
        total=len(users)
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Create a new user
    
    **Admin only**
    
    - Checks if email already exists
    - Hashes the password
    - Creates user with initial password
    - Logs action in audit_log
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    timestamp = get_iso_timestamp()
    new_user = User(
        id=generate_id(),
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        is_active=1,  # Active by default
        last_login_at=None,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    db.add(new_user)
    
    # Create audit log
    create_audit_log(
        db=db,
        entity=ENTITY_USERS,
        entity_id=new_user.id,
        action="create",
        user_id=current_user.id,
        after_data={
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role,
            "is_active": True
        }
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"User created by {current_user.email}: {new_user.email} ({new_user.role})")
    
    return UserResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,
        role=new_user.role,
        is_active=True,
        last_login_at=new_user.last_login_at,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at
    )


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Update user information
    
    **Admin only**
    
    Can update:
    - name
    - email
    - role
    - is_active (activate/deactivate)
    
    Uses logical deletion (is_active) - never deletes users
    """
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Store before state
    before_data = {
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active == 1
    }
    
    # Update fields if provided
    if user_data.name is not None:
        user.name = user_data.name
    
    if user_data.email is not None:
        # Check if new email already exists (excluding current user)
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        user.email = user_data.email
    
    if user_data.role is not None:
        user.role = user_data.role
    
    if user_data.is_active is not None:
        user.is_active = 1 if user_data.is_active else 0
    
    user.updated_at = get_iso_timestamp()
    
    # Store after state
    after_data = {
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active == 1
    }
    
    # Determine action for audit log
    action = "update"
    if before_data["is_active"] != after_data["is_active"]:
        action = "activate" if after_data["is_active"] else "deactivate"
    
    # Create audit log
    create_audit_log(
        db=db,
        entity=ENTITY_USERS,
        entity_id=user.id,
        action=action,
        user_id=current_user.id,
        before_data=before_data,
        after_data=after_data
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(user)
    
    logger.info(f"User updated by {current_user.email}: {user.email}")
    
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active == 1,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post("/users/{user_id}/reset-password", response_model=dict)
def reset_user_password(
    user_id: str,
    password_data: UserResetPassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Reset user password
    
    **Admin only**
    
    Sets a new password for the user
    """
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.password_hash = hash_password(password_data.new_password)
    user.updated_at = get_iso_timestamp()
    
    # Create audit log
    create_audit_log(
        db=db,
        entity=ENTITY_USERS,
        entity_id=user.id,
        action="reset_password",
        user_id=current_user.id,
        after_data={
            "email": user.email,
            "password_reset_by": current_user.email
        }
    )
    
    # Single commit at the end
    db.commit()
    
    logger.info(f"Password reset by {current_user.email} for user: {user.email}")
    
    return {
        "message": "Password reset successfully",
        "user_id": user.id,
        "email": user.email
    }
