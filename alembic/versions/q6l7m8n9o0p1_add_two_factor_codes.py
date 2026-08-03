"""add two_factor_codes table (2FA por email para admins)

Revision ID: q6l7m8n9o0p1
Revises: p5k6l7m8n9o0
Create Date: 2026-08-03

"""
from alembic import op
import sqlalchemy as sa

revision = 'q6l7m8n9o0p1'
down_revision = 'p5k6l7m8n9o0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'two_factor_codes',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('code_hash', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_two_factor_codes_user_id', 'two_factor_codes', ['user_id'])


def downgrade():
    op.drop_index('ix_two_factor_codes_user_id', table_name='two_factor_codes')
    op.drop_table('two_factor_codes')
