"""add_hold_stage

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-04-13 00:00:00.000000

Sprint 4C — Stage "Stand-by / Hold" en cfg_stages
  sort_order=75 (entre Negociación ~70 y Ganado ~80)
  probabilidad por defecto: 20%
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone
import uuid


revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

HOLD_STAGE_ID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "crm.sprint4.stage.hold"))


def upgrade() -> None:
    now = datetime.now(timezone.utc).isoformat()

    # Insertar el stage hold — solo si no existe ya (idempotente)
    op.execute(f"""
        INSERT INTO cfg_stages (id, key, name, description, sort_order, outcome, is_terminal, is_active, created_at, updated_at)
        SELECT
            '{HOLD_STAGE_ID}',
            'hold',
            'Stand-by / Hold',
            'Oportunidad en pausa — el cliente no avanza activamente. Mantener en radar.',
            75,
            'open',
            0,
            1,
            '{now}',
            '{now}'
        WHERE NOT EXISTS (SELECT 1 FROM cfg_stages WHERE key = 'hold')
    """)

    # Insertar probabilidad por defecto: 20%
    op.execute(f"""
        INSERT INTO cfg_stage_probabilities (stage_id, probability, created_at, updated_at)
        SELECT '{HOLD_STAGE_ID}', 0.20, '{now}', '{now}'
        WHERE NOT EXISTS (SELECT 1 FROM cfg_stage_probabilities WHERE stage_id = '{HOLD_STAGE_ID}')
    """)


def downgrade() -> None:
    op.execute(f"DELETE FROM cfg_stage_probabilities WHERE stage_id = '{HOLD_STAGE_ID}'")
    op.execute(f"DELETE FROM cfg_stages WHERE key = 'hold'")
