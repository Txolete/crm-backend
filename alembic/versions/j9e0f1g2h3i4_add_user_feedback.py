"""add user_feedback table

Revision ID: j9e0f1g2h3i4
Revises: i8d9e0f1g2h3
Create Date: 2026-06-12

"""
from alembic import op
import sqlalchemy as sa

revision = 'j9e0f1g2h3i4'
down_revision = 'i8d9e0f1g2h3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user_feedback',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('view', sa.String(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('admin_note', sa.Text(), nullable=True),
    )
    op.create_index('ix_user_feedback_status', 'user_feedback', ['status'])
    op.create_index('ix_user_feedback_user_id', 'user_feedback', ['user_id'])


def downgrade():
    op.drop_index('ix_user_feedback_user_id', table_name='user_feedback')
    op.drop_index('ix_user_feedback_status', table_name='user_feedback')
    op.drop_table('user_feedback')
