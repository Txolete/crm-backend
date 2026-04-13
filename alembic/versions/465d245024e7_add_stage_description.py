"""add_stage_description

Revision ID: 465d245024e7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-13 16:15:30.849147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '465d245024e7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Sprint 3 — U5: añadir columna description a cfg_stages
    op.add_column('cfg_stages', sa.Column('description', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('cfg_stages', 'description')
