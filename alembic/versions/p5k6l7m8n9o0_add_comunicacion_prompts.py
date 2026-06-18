"""add comunicacion_prompts (versiones de prompt + hero level + calibracion)

Revision ID: p5k6l7m8n9o0
Revises: o4j5k6l7m8n9
Create Date: 2026-06-18

"""
from alembic import op
import sqlalchemy as sa

revision = 'p5k6l7m8n9o0'
down_revision = 'o4j5k6l7m8n9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'comunicacion_prompts',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('nombre', sa.String(), nullable=False),
        sa.Column('canal', sa.String(), nullable=False, server_default='correo'),
        sa.Column('prompt_text', sa.Text(), nullable=True),
        sa.Column('hero_level', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('calibracion', sa.Text(), nullable=True),
        sa.Column('activa', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table('comunicacion_prompts')
