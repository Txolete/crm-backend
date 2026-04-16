"""add_cfg_opportunity_types_lost_reasons_mental_states

Revision ID: b1c2d3e4f5a6
Revises: 465d245024e7
Create Date: 2026-04-13 00:00:00.000000

Sprint 4A — Nuevas tablas de configuración:
  - cfg_opportunity_types
  - cfg_lost_reasons
  - cfg_client_mental_states
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = '465d245024e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _now():
    return datetime.now(timezone.utc).isoformat()


def _id(suffix):
    """Genera IDs deterministas para los datos iniciales"""
    import uuid
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"crm.sprint4.{suffix}"))


def upgrade() -> None:
    # ── cfg_opportunity_types ──────────────────────────────────────────────
    op.create_table(
        'cfg_opportunity_types',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # Datos iniciales
    now = _now()
    op.execute(f"""
        INSERT INTO cfg_opportunity_types (id, name, is_active, sort_order, created_at, updated_at) VALUES
        ('{_id("ot1")}', 'Suministro eléctrico', 1, 10, '{now}', '{now}'),
        ('{_id("ot2")}', 'Gas natural', 1, 20, '{now}', '{now}'),
        ('{_id("ot3")}', 'Servicios energéticos', 1, 30, '{now}', '{now}'),
        ('{_id("ot4")}', 'Energías renovables', 1, 40, '{now}', '{now}'),
        ('{_id("ot5")}', 'Consultoría energética', 1, 50, '{now}', '{now}')
    """)

    # ── cfg_lost_reasons ───────────────────────────────────────────────────
    op.create_table(
        'cfg_lost_reasons',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.execute(f"""
        INSERT INTO cfg_lost_reasons (id, name, is_active, sort_order, created_at, updated_at) VALUES
        ('{_id("lr1")}', 'Competencia', 1, 10, '{now}', '{now}'),
        ('{_id("lr2")}', 'Precio', 1, 20, '{now}', '{now}'),
        ('{_id("lr3")}', 'Timing', 1, 30, '{now}', '{now}'),
        ('{_id("lr4")}', 'Presupuesto insuficiente', 1, 40, '{now}', '{now}'),
        ('{_id("lr5")}', 'No encaje de producto', 1, 50, '{now}', '{now}'),
        ('{_id("lr6")}', 'Proyecto no lanzado', 1, 60, '{now}', '{now}'),
        ('{_id("lr7")}', 'Sin respuesta del cliente', 1, 70, '{now}', '{now}')
    """)

    # ── cfg_client_mental_states ───────────────────────────────────────────
    op.create_table(
        'cfg_client_mental_states',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.execute(f"""
        INSERT INTO cfg_client_mental_states (id, name, is_active, sort_order, created_at, updated_at) VALUES
        ('{_id("ms1")}', 'Explorando', 1, 10, '{now}', '{now}'),
        ('{_id("ms2")}', 'Validando', 1, 20, '{now}', '{now}'),
        ('{_id("ms3")}', 'Comparando', 1, 30, '{now}', '{now}'),
        ('{_id("ms4")}', 'Decidiendo', 1, 40, '{now}', '{now}'),
        ('{_id("ms5")}', 'Parado', 1, 50, '{now}', '{now}')
    """)


def downgrade() -> None:
    op.drop_table('cfg_client_mental_states')
    op.drop_table('cfg_lost_reasons')
    op.drop_table('cfg_opportunity_types')
