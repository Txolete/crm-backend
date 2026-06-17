"""ensure email_signature, cc_emails, bcc_emails columns exist (idempotent fix)

Revision ID: n3i4j5k6l7m8
Revises: m2h3i4j5k6l7
Create Date: 2026-06-18

La migracion anterior (m2h3i4j5k6l7) podia haberse marcado como aplicada
sin haber anadido las columnas (rollback parcial tras fallar bulk_insert).
Esta usa ADD COLUMN IF NOT EXISTS para garantizar el estado correcto.

"""
from alembic import op


revision = 'n3i4j5k6l7m8'
down_revision = 'm2h3i4j5k6l7'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_signature TEXT")
    op.execute("ALTER TABLE emails_sent ADD COLUMN IF NOT EXISTS cc_emails VARCHAR")
    op.execute("ALTER TABLE emails_sent ADD COLUMN IF NOT EXISTS bcc_emails VARCHAR")


def downgrade():
    # No-op: queremos garantizar la presencia, no la ausencia.
    pass
