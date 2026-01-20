"""
Account endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.account import Account, Contact, ContactChannel
from app.models.opportunity import Opportunity
from app.schemas.account import (
    AccountCreate, AccountUpdate, AccountResponse, 
    AccountListResponse, AccountDetailResponse
)
from app.schemas.contact import ContactResponse, ContactChannelResponse
from app.utils.auth import get_current_user_from_cookie, require_role
from app.utils.audit import create_audit_log, generate_id, get_iso_timestamp, ENTITY_ACCOUNTS
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts", tags=["Accounts"])

# Configure Jinja2 templates
templates = Jinja2Templates(directory="app/templates")


@router.get("/page", response_class=HTMLResponse)
async def accounts_page(request: Request):
    """
    Serve accounts HTML page
    
    **Authentication:** Checked client-side via JavaScript
    **Permissions:** All authenticated users
    """
    return templates.TemplateResponse(
        "accounts.html",
        {"request": request}
    )


@router.get("", response_model=AccountListResponse)
def list_accounts(
    q: Optional[str] = Query(None, description="Search query"),
    status: Optional[str] = Query("active", pattern="^(active|archived|all)$"),
    owner_user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    List accounts with optional filters
    
    **Permissions:** All authenticated users
    """
    query = db.query(Account)
    
    # Filter by status
    if status == "active":
        query = query.filter(Account.status == "active")
    elif status == "archived":
        query = query.filter(Account.status == "archived")
    # 'all' = no filter
    
    # Filter by owner
    if owner_user_id:
        query = query.filter(Account.owner_user_id == owner_user_id)
    
    # Search by name
    if q:
        query = query.filter(Account.name.ilike(f"%{q}%"))
    
    accounts = query.all()
    
    # Build response with counters
    accounts_with_counts = []
    for acc in accounts:
        # Count opportunities
        opportunities_count = db.query(Opportunity).filter(
            Opportunity.account_id == acc.id
        ).count()
        
        # Count contacts
        contacts_count = db.query(Contact).filter(
            Contact.account_id == acc.id
        ).count()
        
        # Create dict from account
        acc_dict = {
            "id": acc.id,
            "name": acc.name,
            "website": acc.website,
            "phone": acc.phone,
            "email": acc.email,
            "address": acc.address,
            "tax_id": acc.tax_id,
            "region_id": acc.region_id,
            "region_other_text": acc.region_other_text,
            "customer_type_id": acc.customer_type_id,
            "customer_type_other_text": acc.customer_type_other_text,
            "lead_source_id": acc.lead_source_id,
            "lead_source_detail": acc.lead_source_detail,
            "owner_user_id": acc.owner_user_id,
            "status": acc.status,
            "notes": acc.notes,
            "created_at": acc.created_at,
            "updated_at": acc.updated_at,
            "opportunities_count": opportunities_count,
            "contacts_count": contacts_count
        }
        accounts_with_counts.append(AccountResponse(**acc_dict))
    
    return AccountListResponse(
        accounts=accounts_with_counts,
        total=len(accounts)
    )


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Create a new account
    
    **Permissions:** admin, sales
    """
    timestamp = get_iso_timestamp()
    
    new_account = Account(
        id=generate_id(),
        name=account_data.name,
        # Contact info
        website=account_data.website,
        phone=account_data.phone,
        email=account_data.email,
        address=account_data.address,
        # Legal/fiscal
        tax_id=account_data.tax_id,
        # Classification
        region_id=account_data.region_id,
        region_other_text=account_data.region_other_text,
        customer_type_id=account_data.customer_type_id,
        customer_type_other_text=account_data.customer_type_other_text,
        lead_source_id=account_data.lead_source_id,
        lead_source_detail=account_data.lead_source_detail,
        # Management
        owner_user_id=account_data.owner_user_id,
        status="active",
        # Notes
        notes=account_data.notes,
        # Audit
        created_at=timestamp,
        updated_at=timestamp
    )
    
    db.add(new_account)
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_ACCOUNTS,
        entity_id=new_account.id,
        action="create",
        user_id=current_user.id,
        after_data={
            "name": new_account.name,
            "owner_user_id": new_account.owner_user_id,
            "status": new_account.status
        }
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(new_account)
    
    logger.info(f"Account created: {new_account.id} by {current_user.email}")
    
    return AccountResponse.model_validate(new_account)


@router.get("/{account_id}", response_model=AccountDetailResponse)
def get_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Get account detail with contacts, opportunities and stats
    
    **Permissions:** All authenticated users
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Get contacts with their channels
    contacts = db.query(Contact).filter(
        Contact.account_id == account_id,
        Contact.status == 'active'
    ).all()
    
    contacts_data = []
    for contact in contacts:
        channels = db.query(ContactChannel).filter(
            ContactChannel.contact_id == contact.id
        ).all()
        
        contact_dict = ContactResponse.model_validate(contact).model_dump()
        contact_dict['channels'] = [
            ContactChannelResponse.model_validate(ch).model_dump() 
            for ch in channels
        ]
        contacts_data.append(contact_dict)
    
    # Get opportunities (basic info)
    opportunities = db.query(Opportunity).filter(
        Opportunity.account_id == account_id,
        Opportunity.status == 'active'
    ).all()
    
    # Calculate stats
    opportunities_count = len(opportunities)
    contacts_count = len(contacts)
    pipeline_total = sum(
        opp.expected_value_eur 
        for opp in opportunities 
        if opp.close_outcome == 'open'
    )
    
    # Build response
    account_dict = AccountResponse.model_validate(account).model_dump()
    account_dict['opportunities_count'] = opportunities_count
    account_dict['contacts_count'] = contacts_count
    account_dict['pipeline_total'] = pipeline_total
    account_dict['contacts'] = contacts_data
    account_dict['opportunities'] = [
        {
            'id': opp.id,
            'name': opp.name,
            'expected_value_eur': opp.expected_value_eur,
            'stage_id': opp.stage_id,
            'close_outcome': opp.close_outcome
        }
        for opp in opportunities
    ]
    
    return account_dict


@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: str,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Update account
    
    **Permissions:** admin, sales
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Store before state
    before_data = {
        "name": account.name,
        "owner_user_id": account.owner_user_id,
        "region_id": account.region_id,
        "customer_type_id": account.customer_type_id
    }
    
    # Update fields
    if account_data.name is not None:
        account.name = account_data.name
    
    # Contact info
    if account_data.website is not None:
        account.website = account_data.website
    if account_data.phone is not None:
        account.phone = account_data.phone
    if account_data.email is not None:
        account.email = account_data.email
    if account_data.address is not None:
        account.address = account_data.address
    
    # Legal/fiscal
    if account_data.tax_id is not None:
        account.tax_id = account_data.tax_id
    
    # Classification
    if account_data.region_id is not None:
        account.region_id = account_data.region_id
    if account_data.region_other_text is not None:
        account.region_other_text = account_data.region_other_text
    if account_data.customer_type_id is not None:
        account.customer_type_id = account_data.customer_type_id
    if account_data.customer_type_other_text is not None:
        account.customer_type_other_text = account_data.customer_type_other_text
    if account_data.lead_source_id is not None:
        account.lead_source_id = account_data.lead_source_id
    if account_data.lead_source_detail is not None:
        account.lead_source_detail = account_data.lead_source_detail
    
    # Management
    if account_data.owner_user_id is not None:
        account.owner_user_id = account_data.owner_user_id
    if account_data.status is not None:
        account.status = account_data.status
        logger.info(f"[STATUS] Account {account.id} status changed to {account_data.status}")
    
    # Notes
    if account_data.notes is not None:
        account.notes = account_data.notes
    
    account.updated_at = get_iso_timestamp()
    
    # Store after state
    after_data = {
        "name": account.name,
        "owner_user_id": account.owner_user_id,
        "region_id": account.region_id,
        "customer_type_id": account.customer_type_id
    }
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_ACCOUNTS,
        entity_id=account.id,
        action="update",
        user_id=current_user.id,
        before_data=before_data,
        after_data=after_data
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(account)
    
    logger.info(f"Account updated: {account.id} by {current_user.email}")
    
    return AccountResponse.model_validate(account)


@router.post("/{account_id}/archive", response_model=AccountResponse)
def archive_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Archive account (logical deletion)
    
    **Permissions:** admin, sales
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    if account.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already archived"
        )
    
    account.status = "archived"
    account.updated_at = get_iso_timestamp()
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_ACCOUNTS,
        entity_id=account.id,
        action="archive",
        user_id=current_user.id,
        after_data={
            "name": account.name,
            "status": "archived"
        }
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(account)
    
    logger.info(f"Account archived: {account.id} by {current_user.email}")
    
    return AccountResponse.model_validate(account)


@router.post("/{account_id}/restore", response_model=AccountResponse)
def restore_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales"))
):
    """
    Restore archived account
    
    **Permissions:** admin, sales
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    if account.status == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already active"
        )
    
    account.status = "active"
    account.updated_at = get_iso_timestamp()
    
    # Audit log
    create_audit_log(
        db=db,
        entity=ENTITY_ACCOUNTS,
        entity_id=account.id,
        action="restore",
        user_id=current_user.id,
        after_data={
            "name": account.name,
            "status": "active"
        }
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(account)
    
    logger.info(f"Account restored: {account.id} by {current_user.email}")
    
    return AccountResponse.model_validate(account)
