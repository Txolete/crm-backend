"""add material_documents table

Revision ID: k0f1g2h3i4j5
Revises: j9e0f1g2h3i4
Create Date: 2026-06-12

"""
from alembic import op
import sqlalchemy as sa

revision = 'k0f1g2h3i4j5'
down_revision = 'j9e0f1g2h3i4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'material_documents',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('name_slug', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('usage_note', sa.Text(), nullable=True),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_data', sa.LargeBinary(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('uploaded_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('retired_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retired_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
    )
    op.create_index('ix_material_documents_status', 'material_documents', ['status'])
    op.create_index('ix_material_documents_name_slug', 'material_documents', ['name_slug'])


def downgrade():
    op.drop_index('ix_material_documents_name_slug', table_name='material_documents')
    op.drop_index('ix_material_documents_status', table_name='material_documents')
    op.drop_table('material_documents')
