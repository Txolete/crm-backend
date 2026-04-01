from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint
from datetime import datetime, timezone
from app.database import Base


class Account(Base):
    """
    Tabla: accounts
    Clientes/empresas
    """
    __tablename__ = "accounts"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)

    # Contact info
    website = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)

    # Legal/fiscal
    tax_id = Column(String, nullable=True)  # CIF/NIF

    # Classification
    region_id = Column(String, nullable=True)
    region_other_text = Column(String, nullable=True)
    customer_type_id = Column(String, nullable=True)
    customer_type_other_text = Column(String, nullable=True)
    lead_source_id = Column(String, nullable=True)
    lead_source_detail = Column(String, nullable=True)

    # Management
    owner_user_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default='active')

    # Notes
    notes = Column(String, nullable=True)

    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("status IN ('active', 'archived')", name='check_account_status'),
    )


class Contact(Base):
    """
    Tabla: contacts
    Contactos de los accounts
    """
    __tablename__ = "contacts"

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey('accounts.id'), nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    contact_role_id = Column(String, nullable=True)
    contact_role_other_text = Column(String, nullable=True)
    status = Column(String, nullable=False, default='active')
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("status IN ('active', 'archived')", name='check_contact_status'),
    )


class ContactChannel(Base):
    """
    Tabla: contact_channels
    Emails y telefonos de los contactos
    """
    __tablename__ = "contact_channels"

    id = Column(String, primary_key=True)
    contact_id = Column(String, ForeignKey('contacts.id'), nullable=False)
    type = Column(String, nullable=False)
    value = Column(String, nullable=False)
    is_primary = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("type IN ('email', 'phone')", name='check_type'),
    )
