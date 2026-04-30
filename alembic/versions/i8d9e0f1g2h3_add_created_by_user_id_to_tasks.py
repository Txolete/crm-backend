"""add created_by_user_id to tasks

Revision ID: i8d9e0f1g2h3
Revises: h7c8d9e0f1g2
Create Date: 2026-04-30

"""
from alembic import op
import sqlalchemy as sa

revision = 'i8d9e0f1g2h3'
down_revision = 'h7c8d9e0f1g2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tasks',
        sa.Column('created_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True)
    )


def downgrade():
    op.drop_column('tasks', 'created_by_user_id')
