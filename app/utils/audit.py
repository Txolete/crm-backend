"""
Audit log utilities
"""
import uuid
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from typing import Optional


# AUDIT ENTITY CONSTANTS
# These are the exact entity names used in audit_log table
ENTITY_ACCOUNTS = "accounts"
ENTITY_CONTACTS = "contacts"
ENTITY_CONTACT_CHANNELS = "contact_channels"
ENTITY_OPPORTUNITIES = "opportunities"
ENTITY_TASKS = "tasks"
ENTITY_ACTIVITIES = "activities"
ENTITY_USERS = "users"  # For auth/admin operations


def generate_id() -> str:
    """Generate UUID for IDs"""
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    """Get current UTC datetime (timezone-aware)"""
    return datetime.now(tz=__import__('datetime').timezone.utc)


def get_iso_timestamp() -> str:
    """Get current timestamp in ISO format (for JSON responses / logs)"""
    return get_utc_now().isoformat()


def create_audit_log(
    db: Session,
    entity: str,
    entity_id: str,
    action: str,
    user_id: Optional[str] = None,
    before_data: Optional[dict] = None,
    after_data: Optional[dict] = None
) -> AuditLog:
    """
    Create an audit log entry
    
    IMPORTANT: This function does NOT commit the transaction.
    It only adds the audit log entry and flushes to get the ID.
    The caller is responsible for committing the transaction.
    
    This ensures that if the main operation fails and is rolled back,
    the audit log is also rolled back (atomicity).
    
    Args:
        db: Database session
        entity: Entity type (use ENTITY_* constants)
        entity_id: ID of the entity being modified
        action: Action performed (e.g., 'create', 'update', 'login', 'archive', 'restore')
        user_id: ID of the user performing the action (None for system actions)
        before_data: State before the action (for updates)
        after_data: State after the action
        
    Returns:
        AuditLog entry (not yet committed)
    """
    audit_entry = AuditLog(
        id=generate_id(),
        entity=entity,
        entity_id=entity_id,
        action=action,
        before_json=json.dumps(before_data) if before_data else None,
        after_json=json.dumps(after_data) if after_data else None,
        user_id=user_id,
        timestamp=get_utc_now()
    )
    
    db.add(audit_entry)
    db.flush()  # Flush to get ID, but don't commit yet
    
    return audit_entry
