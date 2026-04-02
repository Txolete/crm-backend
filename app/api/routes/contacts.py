"""
Contact and ContactChannel endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.account import Contact, ContactChannel
from app.schemas.contact import (
    ContactCreate, ContactUpdate, ContactResponse, ContactListResponse,
    ContactChannelCreate, ContactChannelUpdate, ContactChannelResponse
)
from app.utils.auth import get_current_user_from_cookie, require_role
from app.utils.audit import (
    create_audit_log,
    generate_id,
    get_iso_timestamp,
    get_utc_now,
    ENTITY_CONTACTS,
    ENTITY_CONTACT_CHANNELS
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.get("/accounts/{account_id}/contacts", response_model=ContactListResponse)
def list_contacts_by_account(
    account_id: str,
    status: Optional[str] = Query("active", pattern="^(active|archived|all)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    List contacts for an account
    
    **Permissions:** All authenticated users
    """
    query = db.query(Contact).filter(Contact.account_id == account_id)
    
    # Filter by status
    if status == "active":
        query = query.filter(Contact.status == "active")
    elif status == "archived":
        query = query.filter(Contact.status == "archived")
    
    contacts = query.all()
    
    # Load channels for each contact
    contacts_with_channels = []
    for contact in contacts:
        channels = db.query(ContactChannel).filter(
            ContactChannel.contact_id == contact.id
        ).all()
        
        contact_dict = ContactResponse.model_validate(contact).model_dump()
        contact_dict['channels'] = [
            ContactChannelResponse.model_validate(ch) for ch in channels
        ]
        contacts_with_channels.append(ContactResponse(**contact_dict))
    
    return ContactListResponse(
        contacts=contacts_with_channels,
        total=len(contacts_with_channels)
    )


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_contact(
    contact_data: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Create a new contact with optional channels
    
    **Permissions:** admin, sales
    """
    timestamp = get_utc_now()
    
    new_contact = Contact(
        id=generate_id(),
        account_id=contact_data.account_id,
        first_name=contact_data.first_name,
        last_name=contact_data.last_name,
        contact_role_id=contact_data.contact_role_id,
        contact_role_other_text=contact_data.contact_role_other_text,
        status="active",
        created_at=timestamp,
        updated_at=timestamp
    )
    
    db.add(new_contact)
    
    # Create channels if provided
    channels = []
    for channel_data in contact_data.channels or []:
        new_channel = ContactChannel(
            id=generate_id(),
            contact_id=new_contact.id,
            type=channel_data.type,
            value=channel_data.value,
            is_primary=1 if channel_data.is_primary else 0,
            created_at=timestamp
        )
        db.add(new_channel)
        channels.append(new_channel)
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_CONTACTS,
        entity_id=new_contact.id,
        action="create",
        user_id=current_user.id,
        after_data={
            "account_id": new_contact.account_id,
            "first_name": new_contact.first_name,
            "last_name": new_contact.last_name,
            "status": new_contact.status,
            "channels_count": len(channels)
        }
    )
    
    # Single commit at the end
    db.commit()
    
    logger.info(f"Contact created: {new_contact.id} by {current_user.email}")
    
    # Return with channels
    contact_dict = ContactResponse.model_validate(new_contact).model_dump()
    contact_dict['channels'] = [
        ContactChannelResponse.model_validate(ch) for ch in channels
    ]
    
    return ContactResponse(**contact_dict)


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get contact by ID with channels
    
    **Permissions:** All authenticated users
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Load channels
    channels = db.query(ContactChannel).filter(
        ContactChannel.contact_id == contact.id
    ).all()
    
    contact_dict = ContactResponse.model_validate(contact).model_dump()
    contact_dict['channels'] = [
        ContactChannelResponse.model_validate(ch) for ch in channels
    ]
    
    return ContactResponse(**contact_dict)


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: str,
    contact_data: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Update contact and optionally replace all channels
    
    **Permissions:** admin, sales
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Store before state
    before_data = {
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "contact_role_id": contact.contact_role_id
    }
    
    # Update fields
    if contact_data.first_name is not None:
        contact.first_name = contact_data.first_name
    if contact_data.last_name is not None:
        contact.last_name = contact_data.last_name
    if contact_data.contact_role_id is not None:
        contact.contact_role_id = contact_data.contact_role_id
    if contact_data.contact_role_other_text is not None:
        contact.contact_role_other_text = contact_data.contact_role_other_text
    
    contact.updated_at = get_utc_now()
    
    # Handle channels if provided
    new_channels = []
    if contact_data.channels is not None:
        # Delete all existing channels
        db.query(ContactChannel).filter(ContactChannel.contact_id == contact_id).delete()
        
        # Create new channels
        timestamp = get_utc_now()
        for channel_data in contact_data.channels:
            new_channel = ContactChannel(
                id=generate_id(),
                contact_id=contact.id,
                type=channel_data.type,
                value=channel_data.value,
                is_primary=1 if channel_data.is_primary else 0,
                created_at=timestamp
            )
            db.add(new_channel)
            new_channels.append(new_channel)
    
    # Store after state
    after_data = {
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "contact_role_id": contact.contact_role_id,
        "channels_count": len(new_channels) if contact_data.channels is not None else None
    }
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_CONTACTS,
        entity_id=contact.id,
        action="update",
        user_id=current_user.id,
        before_data=before_data,
        after_data=after_data
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(contact)
    
    logger.info(f"Contact updated: {contact.id} by {current_user.email}")
    
    # Return with channels (either new ones or existing)
    if contact_data.channels is not None:
        channels = new_channels
    else:
        channels = db.query(ContactChannel).filter(
            ContactChannel.contact_id == contact.id
        ).all()
    
    contact_dict = ContactResponse.model_validate(contact).model_dump()
    contact_dict['channels'] = [
        ContactChannelResponse.model_validate(ch) for ch in channels
    ]
    
    return ContactResponse(**contact_dict)


@router.post("/{contact_id}/archive", response_model=ContactResponse)
def archive_contact(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Archive contact (logical deletion)
    
    **Permissions:** admin, sales
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    if contact.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact already archived"
        )
    
    contact.status = "archived"
    contact.updated_at = get_utc_now()
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_CONTACTS,
        entity_id=contact.id,
        action="archive",
        user_id=current_user.id,
        after_data={
            "account_id": contact.account_id,
            "status": "archived"
        }
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(contact)
    
    logger.info(f"Contact archived: {contact.id} by {current_user.email}")
    
    # Return with channels
    channels = db.query(ContactChannel).filter(
        ContactChannel.contact_id == contact.id
    ).all()
    
    contact_dict = ContactResponse.model_validate(contact).model_dump()
    contact_dict['channels'] = [
        ContactChannelResponse.model_validate(ch) for ch in channels
    ]
    
    return ContactResponse(**contact_dict)


@router.post("/{contact_id}/restore", response_model=ContactResponse)
def restore_contact(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Restore archived contact
    
    **Permissions:** admin, sales
    """
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    if contact.status == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contact already active"
        )
    
    contact.status = "active"
    contact.updated_at = get_utc_now()
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_CONTACTS,
        entity_id=contact.id,
        action="restore",
        user_id=current_user.id,
        after_data={
            "account_id": contact.account_id,
            "status": "active"
        }
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(contact)
    
    logger.info(f"Contact restored: {contact.id} by {current_user.email}")
    
    # Return with channels
    channels = db.query(ContactChannel).filter(
        ContactChannel.contact_id == contact.id
    ).all()
    
    contact_dict = ContactResponse.model_validate(contact).model_dump()
    contact_dict['channels'] = [
        ContactChannelResponse.model_validate(ch) for ch in channels
    ]
    
    return ContactResponse(**contact_dict)


# ===== CONTACT CHANNELS =====

@router.post("/{contact_id}/channels", response_model=ContactChannelResponse, status_code=status.HTTP_201_CREATED)
def create_contact_channel(
    contact_id: str,
    channel_data: ContactChannelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Create a contact channel (email/phone)
    
    **Permissions:** admin, sales
    """
    # Verify contact exists
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    timestamp = get_utc_now()
    
    new_channel = ContactChannel(
        id=generate_id(),
        contact_id=contact_id,
        type=channel_data.type,
        value=channel_data.value,
        is_primary=1 if channel_data.is_primary else 0,
        created_at=timestamp
    )
    
    db.add(new_channel)
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_CONTACT_CHANNELS,
        entity_id=new_channel.id,
        action="create",
        user_id=current_user.id,
        after_data={
            "contact_id": contact_id,
            "type": new_channel.type,
            "is_primary": new_channel.is_primary == 1
        }
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(new_channel)
    
    logger.info(f"Contact channel created: {new_channel.id} by {current_user.email}")
    
    return ContactChannelResponse.model_validate(new_channel)


@router.put("/channels/{channel_id}", response_model=ContactChannelResponse)
def update_contact_channel(
    channel_id: str,
    channel_data: ContactChannelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Update contact channel
    
    **Permissions:** admin, sales
    """
    channel = db.query(ContactChannel).filter(ContactChannel.id == channel_id).first()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact channel not found"
        )
    
    # Store before state
    before_data = {
        "value": channel.value,
        "is_primary": channel.is_primary == 1
    }
    
    # Update fields
    if channel_data.value is not None:
        channel.value = channel_data.value
    if channel_data.is_primary is not None:
        channel.is_primary = 1 if channel_data.is_primary else 0
    
    # Store after state
    after_data = {
        "value": channel.value,
        "is_primary": channel.is_primary == 1
    }
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_CONTACT_CHANNELS,
        entity_id=channel.id,
        action="update",
        user_id=current_user.id,
        before_data=before_data,
        after_data=after_data
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(channel)
    
    logger.info(f"Contact channel updated: {channel.id} by {current_user.email}")
    
    return ContactChannelResponse.model_validate(channel)


@router.delete("/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact_channel(
    channel_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Delete contact channel (physical deletion - exception to logical deletion rule)
    
    **Permissions:** admin, sales
    
    **Note:** ContactChannels do not have status field, so physical deletion is allowed
    """
    channel = db.query(ContactChannel).filter(ContactChannel.id == channel_id).first()
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact channel not found"
        )
    
    # Audit log before deletion
    create_audit_log(
        db=db,
        entity=ENTITY_CONTACT_CHANNELS,
        entity_id=channel.id,
        action="delete",
        user_id=current_user.id,
        before_data={
            "contact_id": channel.contact_id,
            "type": channel.type,
            "value": channel.value
        }
    )
    
    db.delete(channel)
    
    # Single commit at the end
    db.commit()
    
    logger.info(f"Contact channel deleted: {channel_id} by {current_user.email}")
    
    return None
