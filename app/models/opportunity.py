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
    lost_reason = Column(String, nullable=True)  # legacy — usar lost_reason_id para nuevas pérdidas
    owner_user_id = Column(String, ForeignKey('users.id'), nullable=True)
    status = Column(String, nullable=False, default='active')

    # Sprint 4B — nuevos campos de inteligencia comercial y AI
    opportunity_type_id = Column(String, ForeignKey('cfg_opportunity_types.id'), nullable=True)
    client_mental_state_id = Column(String, ForeignKey('cfg_client_mental_states.id'), nullable=True)
    strategic_objective = Column(String, nullable=True)
    next_strategic_action = Column(String, nullable=True)
    executive_summary = Column(String, nullable=True)
    lost_reason_id = Column(String, ForeignKey('cfg_lost_reasons.id'), nullable=True)
    lost_reason_detail = Column(String, nullable=True)
    hold_reason = Column(String, nullable=True)
    chatgpt_thread_id = Column(String(200), nullable=True)
    chatgpt_url = Column(String(500), nullable=True)
    # Sprint 4E v2 — historial chat IA y notas de sesión externa
    ai_chat_history = Column(String, nullable=True)       # JSON array de Q&A
    external_session_notes = Column(String, nullable=True) # conclusiones copiadas de ChatGPT Pro / Claude
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


class OpportunityOutcome(Base):
    """
    Tabla: opportunity_outcomes
    Sprint 5B — Snapshot de una oportunidad al cierre (ganada o perdida).
    Base de datos de aprendizaje para el agente de Memoria Corporativa.
    """
    __tablename__ = "opportunity_outcomes"

    id = Column(String, primary_key=True)
    opportunity_id = Column(String, ForeignKey('opportunities.id'), nullable=False)

    # Resultado del cierre
    outcome = Column(String, nullable=False)            # 'won' | 'lost'
    close_date = Column(UTCDateTime(), nullable=True)
    final_value_eur = Column(Float, nullable=True)
    lost_reason_id = Column(String, ForeignKey('cfg_lost_reasons.id'), nullable=True)
    lost_reason_detail = Column(String, nullable=True)

    # Snapshot de contexto al cierre
    account_name = Column(String, nullable=True)
    opportunity_name = Column(String, nullable=True)
    opportunity_type = Column(String, nullable=True)    # nombre del tipo
    stage_at_close = Column(String, nullable=True)      # nombre del stage final
    days_in_pipeline = Column(Integer, nullable=True)   # días desde creación hasta cierre
    activity_count = Column(Integer, nullable=True)
    task_count = Column(Integer, nullable=True)
    final_probability = Column(Float, nullable=True)    # 0-1
    client_mental_state = Column(String, nullable=True)
    strategic_objective = Column(String, nullable=True)
    executive_summary_at_close = Column(String, nullable=True)

    # Sprint 5D — Feedback loop (retrospectiva del comercial)
    retro_what_worked = Column(String, nullable=True)   # qué funcionó
    retro_what_failed = Column(String, nullable=True)   # qué no funcionó
    retro_ai_useful = Column(String, nullable=True)     # 'yes' | 'no' | 'partial'
    retro_notes = Column(String, nullable=True)         # texto libre

    owner_user_id = Column(String, ForeignKey('users.id'), nullable=True)
    created_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("outcome IN ('won', 'lost')", name='check_outcome_result'),
    )
