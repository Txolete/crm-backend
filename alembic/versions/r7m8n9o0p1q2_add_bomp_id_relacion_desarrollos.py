"""add bomp_id y FK relacionado_con a desarrollos

Revision ID: r7m8n9o0p1q2
Revises: q6l7m8n9o0p1
Create Date: 2026-08-17

"""
from alembic import op
import sqlalchemy as sa

revision = 'r7m8n9o0p1q2'
down_revision = 'q6l7m8n9o0p1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('desarrollos', sa.Column('bomp_id', sa.Integer(), nullable=True))
    op.create_unique_constraint('uq_desarrollos_bomp_id', 'desarrollos', ['bomp_id'])
    op.create_index('ix_desarrollos_bomp_id', 'desarrollos', ['bomp_id'])
    op.create_foreign_key(
        'fk_desarrollos_relacionado_con', 'desarrollos', 'desarrollos',
        ['relacionado_con'], ['id'],
    )


def downgrade():
    op.drop_constraint('fk_desarrollos_relacionado_con', 'desarrollos', type_='foreignkey')
    op.drop_index('ix_desarrollos_bomp_id', table_name='desarrollos')
    op.drop_constraint('uq_desarrollos_bomp_id', 'desarrollos', type_='unique')
    op.drop_column('desarrollos', 'bomp_id')
