"""user signature + email cc/bcc + nuevos roles de contacto

Revision ID: m2h3i4j5k6l7
Revises: l1g2h3i4j5k6
Create Date: 2026-06-17

"""
from alembic import op
import sqlalchemy as sa
import uuid
from datetime import datetime, timezone

revision = 'm2h3i4j5k6l7'
down_revision = 'l1g2h3i4j5k6'
branch_labels = None
depends_on = None


NEW_CONTACT_ROLES = [
    "Centralita / Recepción",
    "Secretari@",
    "Empleado de proximidad al responsable",
    "Responsable Back Office",
]


def upgrade():
    # 1) email_signature en users
    op.add_column('users', sa.Column('email_signature', sa.Text(), nullable=True))

    # 2) cc / bcc en emails_sent
    op.add_column('emails_sent', sa.Column('cc_emails', sa.String(), nullable=True))
    op.add_column('emails_sent', sa.Column('bcc_emails', sa.String(), nullable=True))

    # 3) nuevos roles de contacto (idempotente: solo inserta si no existen)
    bind = op.get_bind()
    existing = {r[0] for r in bind.execute(sa.text("SELECT name FROM cfg_contact_roles")).fetchall()}
    cfg_table = sa.table(
        'cfg_contact_roles',
        sa.column('id', sa.String),
        sa.column('name', sa.String),
        sa.column('sort_order', sa.Integer),
        sa.column('is_active', sa.Integer),
        sa.column('created_at', sa.DateTime(timezone=True)),
        sa.column('updated_at', sa.DateTime(timezone=True)),
    )

    # encontrar el sort_order maximo actual
    max_order = bind.execute(sa.text("SELECT COALESCE(MAX(sort_order), 0) FROM cfg_contact_roles")).scalar() or 0
    now = datetime.now(timezone.utc)
    rows = []
    for i, name in enumerate(NEW_CONTACT_ROLES, start=1):
        if name in existing:
            continue
        rows.append({
            'id': str(uuid.uuid4()),
            'name': name,
            'sort_order': max_order + i,
            'is_active': 1,
            'created_at': now,
            'updated_at': now,
        })
    if rows:
        op.bulk_insert(cfg_table, rows)


def downgrade():
    op.drop_column('emails_sent', 'bcc_emails')
    op.drop_column('emails_sent', 'cc_emails')
    op.drop_column('users', 'email_signature')
    # No revertimos los nuevos roles (datos)
