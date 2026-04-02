"""add_commercial_role

Revision ID: a1b2c3d4e5f6
Revises: 9cdeb178b880
Create Date: 2026-04-01 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9cdeb178b880'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite does not support DROP CONSTRAINT / ADD CONSTRAINT — skip for SQLite.
    # On PostgreSQL, drop old check and add new one that includes 'commercial'.
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.drop_constraint('check_role', 'users', type_='check')
        op.create_check_constraint(
            'check_role',
            'users',
            "role IN ('admin', 'sales', 'commercial', 'viewer')"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.drop_constraint('check_role', 'users', type_='check')
        op.create_check_constraint(
            'check_role',
            'users',
            "role IN ('admin', 'sales', 'viewer')"
        )
