from sqlalchemy import Column, String, Float, Integer, Date, ForeignKey, CheckConstraint
from datetime import datetime, timezone
from app.database import Base, UTCDateTime


class Opportunity(Base):
    """
    Tabla: opportunities
    Oportunidades comerciales
    """
    __tablename__ = "opportunities"

    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey('accounts.id'), nullable=False)
    name = Column(String, nullable=True)
    stage_id = Column(String, ForeignKey('cfg_stages.id'), nullable=False)
    stage_detail = Column(String, nullable=True)
    expected_value_eur = Column(Float, nullable=False)
    weighted_value_override_eur = Column(Float, nullable=True)
    probability_override = Column(Float, nullable=True)
    forecast_close_month = Column(String, nullable=True)
    close_outcome = Column(String, nullable=False, default='open')
    close_date = Column(UTCDateTime(), nullable=True)
    won_value_eur = Column(Float, nullable=True)
    lost_reason = Column(String, nullable=True)
    owner_user_id = Column(String, ForeignKey('users.id'), nullable=True)
    status = Column(String, nullable=False, default='active')
    created_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("close_outcome IN ('open', 'won', 'lost')", name='check_close_outcome'),
        CheckConstraint("status IN ('active', 'archived')", name='check_opportunity_status'),
        CheckConstraint("probability_override IS NULL OR (probability_override BETWEEN 0 AND 1)", name='check_probability_override'),
    )


class Task(Base):
    """
    Tabla: tasks
    Tareas/siguiente paso

    Vinculacion flexible:
    - opportunity_id (opcional): tarea vinculada a oportunidad
    - account_id (opcional): tarea vinculada a cuenta
    - Al menos UNO debe estar presente
    """
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    opportunity_id = Column(String, ForeignKey('opportunities.id'), nullable=True)
    account_id = Column(String, ForeignKey('accounts.id'), nullable=True)
    task_template_id = Column(String, ForeignKey('cfg_task_templates.id'), nullable=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    due_date = Column(Date, nullable=True)
    priority = Column(String, nullable=False, default='medium')
    status = Column(String, nullable=False, default='open')
    assigned_to_user_id = Column(String, ForeignKey('users.id'), nullable=True)
    completed_at = Column(UTCDateTime(), nullable=True)
    completed_by_user_id = Column(String, ForeignKey('users.id'), nullable=True)
    reminder_date = Column(UTCDateTime(), nullable=True)
    created_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("status IN ('open', 'in_progress', 'completed', 'cancelled')", name='check_task_status'),
        CheckConstraint("priority IN ('high', 'medium', 'low')", name='check_task_priority'),
        CheckConstraint("opportunity_id IS NOT NULL OR account_id IS NOT NULL", name='check_task_link'),
    )


class Activity(Base):
    """
    Tabla: activities
    Timeline de actividades
    """
    __tablename__ = "activities"

    id = Column(String, primary_key=True)
    opportunity_id = Column(String, ForeignKey('opportunities.id'), nullable=False)
    type = Column(String, nullable=False)
    occurred_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
    summary = Column(String, nullable=False)
    created_by_user_id = Column(String, ForeignKey('users.id'), nullable=True)
    created_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
