"""add_opportunity_outcomes

Sprint 5B — Tabla de aprendizaje: snapshot de cada oportunidad al cierre.
Base para el agente de Memoria Corporativa y el feedback loop (5D).

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-04-16
"""
from alembic import op
import sqlalchemy as sa

revision = 'f5a6b7c8d9e0'
down_revision = 'e4f5a6b7c8d9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'opportunity_outcomes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('opportunity_id', sa.String(), sa.ForeignKey('opportunities.id'), nullable=False),

        # Resultado
        sa.Column('outcome', sa.String(), nullable=False),
        sa.Column('close_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('final_value_eur', sa.Float(), nullable=True),
        sa.Column('lost_reason_id', sa.String(), sa.ForeignKey('cfg_lost_reasons.id'), nullable=True),
        sa.Column('lost_reason_detail', sa.String(), nullable=True),

        # Snapshot contexto
        sa.Column('account_name', sa.String(), nullable=True),
        sa.Column('opportunity_name', sa.String(), nullable=True),
        sa.Column('opportunity_type', sa.String(), nullable=True),
        sa.Column('stage_at_close', sa.String(), nullable=True),
        sa.Column('days_in_pipeline', sa.Integer(), nullable=True),
        sa.Column('activity_count', sa.Integer(), nullable=True),
        sa.Column('task_count', sa.Integer(), nullable=True),
        sa.Column('final_probability', sa.Float(), nullable=True),
        sa.Column('client_mental_state', sa.String(), nullable=True),
        sa.Column('strategic_objective', sa.String(), nullable=True),
        sa.Column('executive_summary_at_close', sa.String(), nullable=True),

        # Feedback loop (5D)
        sa.Column('retro_what_worked', sa.String(), nullable=True),
        sa.Column('retro_what_failed', sa.String(), nullable=True),
        sa.Column('retro_ai_useful', sa.String(), nullable=True),
        sa.Column('retro_notes', sa.String(), nullable=True),

        sa.Column('owner_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("outcome IN ('won', 'lost')", name='check_outcome_result'),
    )
    op.create_index('ix_opportunity_outcomes_opportunity_id', 'opportunity_outcomes', ['opportunity_id'])
    op.create_index('ix_opportunity_outcomes_outcome', 'opportunity_outcomes', ['outcome'])


def downgrade() -> None:
    op.drop_index('ix_opportunity_outcomes_outcome', table_name='opportunity_outcomes')
    op.drop_index('ix_opportunity_outcomes_opportunity_id', table_name='opportunity_outcomes')
    op.drop_table('opportunity_outcomes')
