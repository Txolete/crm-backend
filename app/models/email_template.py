from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean
from datetime import datetime, timezone
from app.database import Base, UTCDateTime


class EmailTemplate(Base):
    """
    Tabla: email_templates
    Plantillas de email comercial (texto plano).
    Variables soportadas: {{nombre}}, {{empresa}}, {{senal_detectada}}, {{firma_comercial}}.
    senal_detectada es obligatoria por defecto (regla de la guia: sin senal, no se envia).
    """
    __tablename__ = "email_templates"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)  # cold-standard | cold-corporate | follow-up | inbound...
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    required_variables = Column(String, nullable=False, default="senal_detectada")  # CSV
    is_active = Column(Integer, nullable=False, default=1)
    notes = Column(Text, nullable=True)  # guidance for the user
    created_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)


class EmailSent(Base):
    """
    Tabla: emails_sent
    Registro de cada email enviado desde una plantilla (o ad-hoc).
    Marcado manual de respuesta hasta que tengamos IMAP/webhook.
    """
    __tablename__ = "emails_sent"

    id = Column(String, primary_key=True)
    template_id = Column(String, ForeignKey("email_templates.id"), nullable=True)
    template_name_snapshot = Column(String, nullable=True)

    account_id = Column(String, ForeignKey("accounts.id"), nullable=True)
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=True)
    opportunity_id = Column(String, ForeignKey("opportunities.id"), nullable=True)

    to_email = Column(String, nullable=False)
    to_name = Column(String, nullable=True)
    cc_emails = Column(String, nullable=True)   # separados por ';' o ','
    bcc_emails = Column(String, nullable=True)  # separados por ';' o ','
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    senal_detectada = Column(Text, nullable=True)

    sent_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
    sent_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)

    response_received = Column(Integer, nullable=False, default=0)  # 0/1
    response_at = Column(UTCDateTime(), nullable=True)
    response_note = Column(Text, nullable=True)
