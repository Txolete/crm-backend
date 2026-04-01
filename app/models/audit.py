from sqlalchemy import Column, String, Float, Integer, DateTime
from datetime import datetime, timezone
from app.database import Base


class AuditLog(Base):
    """
    Tabla: audit_log
    Log de auditoria de todas las acciones
    """
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True)
    entity = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    before_json = Column(String, nullable=True)
    after_json = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class AppVersion(Base):
    """
    Tabla: app_versions
    Registro de versiones de la aplicacion
    """
    __tablename__ = "app_versions"

    id = Column(String, primary_key=True)
    version = Column(String, nullable=False, unique=True)
    release_date = Column(String, nullable=False)
    title = Column(String, nullable=False)
    changes_markdown = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
