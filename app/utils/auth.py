"""
Authentication and Authorization middleware
"""
from fastapi import Depends, HTTPException, status, Request, Cookie
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.utils.security import decode_access_token
from app.config import get_settings

settings = get_settings()


def get_current_user_from_cookie(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from JWT token in HttpOnly cookie
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Get token from cookie using configured cookie name
    access_token = request.cookies.get(settings.cookie_name)
    
    if not access_token:
        raise credentials_exception
    
    # Decode token
    payload = decode_access_token(access_token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


def require_role(*allowed_roles: str):
    """
    Dependency to require specific role(s)
    
    Usage:
        @router.get("/admin/users", dependencies=[Depends(require_role("admin"))])
        
    Args:
        *allowed_roles: One or more roles that are allowed (admin, sales, viewer)
        
    Returns:
        Dependency function
    """
    def role_checker(current_user: User = Depends(get_current_user_from_cookie)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return role_checker


# Role sets
SALES_ROLES = {"admin", "sales", "commercial"}


def is_own_data_only(user: User) -> bool:
    """Return True if this user should only see their own data (commercial role)."""
    return user.role == "commercial"


# Common dependencies
require_auth = Depends(get_current_user_from_cookie)
require_admin = Depends(require_role("admin"))
require_sales_or_admin = Depends(require_role("admin", "sales"))
require_sales_roles = Depends(require_role("admin", "sales", "commercial"))
