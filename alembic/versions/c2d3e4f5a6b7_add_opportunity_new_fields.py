"""add_opportunity_new_fields

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-04-13 00:00:00.000000

Sprint 4B — Nuevas columnas en tabla opportunities:
  - opportunity_type_id (FK cfg_opportunity_types)
  - client_mental_state_id (FK cfg_client_mental_states)
  - strategic_objective
  - next_strategic_action
  - executive_summary
  - lost_reason_id (FK cfg_lost_reasons)
  - lost_reason_detail
  - hold_reason
  - chatgpt_thread_id
  - chatgpt_url
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('opportunities', sa.Column('opportunity_type_id', sa.String(), sa.ForeignKey('cfg_opportunity_types.id'), nullable=True))
    op.add_column('opportunities', sa.Column('client_mental_state_id', sa.String(), sa.ForeignKey('cfg_client_mental_states.id'), nullable=True))
    op.add_column('opportunities', sa.Column('strategic_objective', sa.Text(), nullable=True))
    op.add_column('opportunities', sa.Column('next_strategic_action', sa.Text(), nullable=True))
    op.add_column('opportunities', sa.Column('executive_summary', sa.Text(), nullable=True))
    op.add_column('opportunities', sa.Column('lost_reason_id', sa.String(), sa.ForeignKey('cfg_lost_reasons.id'), nullable=True))
    op.add_column('opportunities', sa.Column('lost_reason_detail', sa.Text(), nullable=True))
    op.add_column('opportunities', sa.Column('hold_reason', sa.Text(), nullable=True))
    op.add_column('opportunities', sa.Column('chatgpt_thread_id', sa.String(200), nullable=True))
    op.add_column('opportunities', sa.Column('chatgpt_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('opportunities', 'chatgpt_url')
    op.drop_column('opportunities', 'chatgpt_thread_id')
    op.drop_column('opportunities', 'hold_reason')
    op.drop_column('opportunities', 'lost_reason_detail')
    op.drop_column('opportunities', 'lost_reason_id')
    op.drop_column('opportunities', 'executive_summary')
    op.drop_column('opportunities', 'next_strategic_action')
    op.drop_column('opportunities', 'strategic_objective')
    op.drop_column('opportunities', 'client_mental_state_id')
    op.drop_column('opportunities', 'opportunity_type_id')
