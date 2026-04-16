"""add_ai_chat_history_external_session_notes

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-04-15 00:00:00.000000

Sprint 4E v2:
  - ai_chat_history: JSON array con historial de Q&A del mini-chat interno
  - external_session_notes: conclusiones copiadas de sesiones externas (ChatGPT Pro, Claude, etc.)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, None] = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('opportunities', sa.Column('ai_chat_history', sa.Text(), nullable=True))
    op.add_column('opportunities', sa.Column('external_session_notes', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('opportunities', 'external_session_notes')
    op.drop_column('opportunities', 'ai_chat_history')
