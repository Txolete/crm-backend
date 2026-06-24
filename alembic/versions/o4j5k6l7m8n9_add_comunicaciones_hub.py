"""add comunicaciones hub (publicaciones, desarrollos, salidas_canal)

Revision ID: o4j5k6l7m8n9
Revises: n3i4j5k6l7m8
Create Date: 2026-06-18

"""
from alembic import op
import sqlalchemy as sa

revision = 'o4j5k6l7m8n9'
down_revision = 'n3i4j5k6l7m8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'publicaciones',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('version_erp', sa.String(), nullable=True),
        sa.Column('fecha_ingesta', sa.DateTime(timezone=True), nullable=False),
        sa.Column('estado', sa.String(), nullable=False, server_default='borrador'),
        sa.Column('created_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
    )

    op.create_table(
        'desarrollos',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('publicacion_id', sa.String(), sa.ForeignKey('publicaciones.id'), nullable=False),
        sa.Column('titulo_crudo', sa.String(), nullable=False),
        sa.Column('tipo', sa.String(), nullable=True),
        sa.Column('fecha', sa.String(), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('modulo', sa.String(), nullable=True),
        sa.Column('origen', sa.String(), nullable=True),
        sa.Column('proyecto', sa.String(), nullable=True),
        sa.Column('norma', sa.String(), nullable=True),
        sa.Column('mantenimiento', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('relacionado_con', sa.String(), nullable=True),
        sa.Column('canales', sa.String(), nullable=True),
        sa.Column('incluir', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('orden', sa.Integer(), nullable=True),
    )
    op.create_index('ix_desarrollos_publicacion_id', 'desarrollos', ['publicacion_id'])

    op.create_table(
        'salidas_canal',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('publicacion_id', sa.String(), sa.ForeignKey('publicaciones.id'), nullable=False),
        sa.Column('canal', sa.String(), nullable=False, server_default='correo'),
        sa.Column('contenido_generado', sa.Text(), nullable=True),
        sa.Column('contenido_editado', sa.Text(), nullable=True),
        sa.Column('estado', sa.String(), nullable=False, server_default='borrador'),
        sa.Column('meta', sa.Text(), nullable=True),
        sa.Column('fecha_publicacion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_salidas_canal_publicacion_id', 'salidas_canal', ['publicacion_id'])


def downgrade():
    op.drop_index('ix_salidas_canal_publicacion_id', table_name='salidas_canal')
    op.drop_table('salidas_canal')
    op.drop_index('ix_desarrollos_publicacion_id', table_name='desarrollos')
    op.drop_table('desarrollos')
    op.drop_table('publicaciones')
