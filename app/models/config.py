from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, CheckConstraint
from datetime import datetime, timezone
from app.database import Base


class CfgRegion(Base):
    """
    Tabla: cfg_regions
    Provincias/regiones
    """
    __tablename__ = "cfg_regions"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    country_code = Column(String, nullable=False, default='ES')
    is_active = Column(Integer, nullable=False, default=1)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CfgCustomerType(Base):
    """
    Tabla: cfg_customer_types
    Tipos de cliente
    """
    __tablename__ = "cfg_customer_types"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    is_active = Column(Integer, nullable=False, default=1)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CfgLeadSource(Base):
    """
    Tabla: cfg_lead_sources
    Canales comerciales / fuentes de leads
    """
    __tablename__ = "cfg_lead_sources"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    category = Column(String, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CfgContactRole(Base):
    """
    Tabla: cfg_contact_roles
    Roles de contacto
    """
    __tablename__ = "cfg_contact_roles"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    is_active = Column(Integer, nullable=False, default=1)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CfgTaskTemplate(Base):
    """
    Tabla: cfg_task_templates
    Plantillas de tareas
    """
    __tablename__ = "cfg_task_templates"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    default_due_days = Column(Integer, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CfgStage(Base):
    """
    Tabla: cfg_stages
    Etapas del pipeline
    """
    __tablename__ = "cfg_stages"

    id = Column(String, primary_key=True)
    key = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    sort_order = Column(Integer, nullable=False)
    outcome = Column(String, nullable=False)
    is_terminal = Column(Integer, nullable=False, default=0)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("outcome IN ('open', 'won', 'lost')", name='check_outcome'),
    )


class CfgStageProbability(Base):
    """
    Tabla: cfg_stage_probabilities
    Probabilidades por stage
    """
    __tablename__ = "cfg_stage_probabilities"

    stage_id = Column(String, ForeignKey('cfg_stages.id'), primary_key=True)
    probability = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("probability BETWEEN 0 AND 1", name='check_probability'),
    )
