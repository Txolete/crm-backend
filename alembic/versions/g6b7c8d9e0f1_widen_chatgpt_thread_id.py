"""widen chatgpt_thread_id to 1000

Sprint 5A — los resp_IDs de la Responses API se guardan como JSON con tres claves
(client, sales, memory) y superan el límite original de VARCHAR(200).

Revision ID: g6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-04-17
"""
from alembic import op
import sqlalchemy as sa

revision = 'g6b7c8d9e0f1'
down_revision = 'f5a6b7c8d9e0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('opportunities') as batch_op:
        batch_op.alter_column(
            'chatgpt_thread_id',
            existing_type=sa.String(200),
            type_=sa.String(1000),
            existing_nullable=True,
        )


def downgrade():
    with op.batch_alter_table('opportunities') as batch_op:
        batch_op.alter_column(
            'chatgpt_thread_id',
            existing_type=sa.String(1000),
            type_=sa.String(200),
            existing_nullable=True,
        )
