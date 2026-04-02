"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse, MeResponse
from app.utils.security import verify_password, create_access_token
from app.utils.auth import get_current_user_from_cookie
from app.utils.audit import create_audit_log, get_iso_timestamp, get_utc_now, ENTITY_USERS
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Login with email and password
    
    Behavior:
    - If email doesn't exist → 401
    - If password incorrect → 401
    - If is_active = false → 403
    - On success:
      - Update last_login_at
      - Set JWT in HttpOnly cookie
      - Return user data (id, name, email, role)
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    # If user doesn't exist → 401
    if not user:
        logger.warning(f"Login attempt with non-existent email: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # If password incorrect → 401
    if not verify_password(credentials.password, user.password_hash):
        logger.warning(f"Failed login attempt for user: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # If user is inactive → 403
    if not user.is_active:
        logger.warning(f"Login attempt by inactive user: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last_login_at
    user.last_login_at = get_utc_now()
    user.updated_at = get_utc_now()
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role}
    )
    
    # Set token in HttpOnly cookie using configuration
    response.set_cookie(
        key=settings.cookie_name,
        value=access_token,
        httponly=True,
        max_age=settings.cookie_max_age,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure
    )
    
    # Create audit log
    create_audit_log(
        db=db,
        entity=ENTITY_USERS,
        entity_id=user.id,
        action="login",
        user_id=user.id,
        after_data={
            "email": user.email,
            "last_login_at": user.last_login_at
        }
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(user)
    
    logger.info(f"User logged in successfully: {user.email}")
    
    return LoginResponse(
        message="Login successful",
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(response: Response):
    """
    Logout by clearing the HttpOnly cookie
    """
    response.delete_cookie(key=settings.cookie_name)
    
    return LogoutResponse(message="Logout successful")


@router.get("/me", response_model=MeResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get current authenticated user information
    
    Protected endpoint - requires valid JWT token in cookie
    """
    return MeResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active == 1,  # Convert INTEGER to bool
        last_login_at=current_user.last_login_at
    )
