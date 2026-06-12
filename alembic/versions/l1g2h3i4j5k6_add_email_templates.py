"""add email_templates + emails_sent + seed initial templates

Revision ID: l1g2h3i4j5k6
Revises: k0f1g2h3i4j5
Create Date: 2026-06-12

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone
import uuid

revision = 'l1g2h3i4j5k6'
down_revision = 'k0f1g2h3i4j5'
branch_labels = None
depends_on = None


COLD_STANDARD_SUBJECT = "Vuestra operativa como comercializadora"
COLD_STANDARD_BODY = """Hola {{nombre}},

He visto que {{senal_detectada}}. Enhorabuena — y prepárate, porque OMIE, REE, las distribuidoras y la CNMC no esperan, y cada cambio regulatorio rompe algo.

A eso nos dedicamos: llevamos el back office de más de 60 comercializadoras desde 2017, con BOMP, nuestro ERP nacido para este mercado. Hay quien nos usa como equipo externo, quien solo usa el software y quien combina ambos.

¿Te encajan 15 minutos esta semana para ver qué encaja en vuestro caso?

{{firma_comercial}}
ASIC XXI"""

COLD_CORPORATE_SUBJECT = "Mercado energético español / apoyo operativo local"
COLD_CORPORATE_BODY = """Hola {{nombre}},

He visto que {{empresa}} opera a una escala muy corporativa en trading, gas, electricidad y soluciones energéticas, así que no tendría sentido plantearos una herramienta genérica ni intentar sustituir sistemas globales.

Donde ASICXXI sí puede aportar valor es en proyectos concretos en Iberia cuando hace falta aterrizar actividad en el mercado español: CNMC, OMIE, REE, MITECO, ENAGAS, CORES, MIBGAS, switching, facturación, reporting, previsión de demanda, gestión de desvíos, garantías y modelo operativo de comercialización, consumidores directos, etc.

Imagino que para consultoría estratégica o regulatoria global ya trabajáis con firmas grandes. Nuestro enfoque es distinto: asesoría senior, muy especializada en operación real de agentes, sin capas de juniors ni estructura pesada de consultora generalista. Menos presentación corporativa y más ejecución práctica: trámites, procesos, sistemas, automatización y puesta en marcha.

Podemos actuar como apoyo especialista local, tanto si se trata de una unidad propia, un partner o un proyecto en España/Iberia que necesite conocimiento operativo del mercado.

{{senal_detectada}}

¿Tiene sentido que lo validemos brevemente, o ahora mismo no tenéis ningún frente activo en esta línea?

Un saludo,
{{firma_comercial}}"""


def upgrade():
    op.create_table(
        'email_templates',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('required_variables', sa.String(), nullable=False, server_default='senal_detectada'),
        sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
    )
    op.create_index('ix_email_templates_category', 'email_templates', ['category'])
    op.create_index('ix_email_templates_is_active', 'email_templates', ['is_active'])

    op.create_table(
        'emails_sent',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('template_id', sa.String(), sa.ForeignKey('email_templates.id'), nullable=True),
        sa.Column('template_name_snapshot', sa.String(), nullable=True),
        sa.Column('account_id', sa.String(), sa.ForeignKey('accounts.id'), nullable=True),
        sa.Column('contact_id', sa.String(), sa.ForeignKey('contacts.id'), nullable=True),
        sa.Column('opportunity_id', sa.String(), sa.ForeignKey('opportunities.id'), nullable=True),
        sa.Column('to_email', sa.String(), nullable=False),
        sa.Column('to_name', sa.String(), nullable=True),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('senal_detectada', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('response_received', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_note', sa.Text(), nullable=True),
    )
    op.create_index('ix_emails_sent_account_id', 'emails_sent', ['account_id'])
    op.create_index('ix_emails_sent_contact_id', 'emails_sent', ['contact_id'])
    op.create_index('ix_emails_sent_template_id', 'emails_sent', ['template_id'])

    # Seed initial templates
    now = datetime.now(timezone.utc)
    op.bulk_insert(
        sa.table(
            'email_templates',
            sa.column('id', sa.String),
            sa.column('name', sa.String),
            sa.column('category', sa.String),
            sa.column('subject', sa.String),
            sa.column('body', sa.Text),
            sa.column('required_variables', sa.String),
            sa.column('is_active', sa.Integer),
            sa.column('notes', sa.Text),
            sa.column('created_at', sa.DateTime(timezone=True)),
            sa.column('updated_at', sa.DateTime(timezone=True)),
        ),
        [
            {
                'id': str(uuid.uuid4()),
                'name': 'Email frío estándar (PYME / mid-market)',
                'category': 'cold-standard',
                'subject': COLD_STANDARD_SUBJECT,
                'body': COLD_STANDARD_BODY,
                'required_variables': 'nombre,senal_detectada,firma_comercial',
                'is_active': 1,
                'notes': 'Comercializadoras pequeñas/medianas. <100 palabras, sin adjuntos, un único CTA: reunión de 15 minutos. Personalizar SIEMPRE la señal detectada (sin señal, no se envía).',
                'created_at': now,
                'updated_at': now,
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Email frío corporate / TIER 1 (Shell, UNIPER, etc.)',
                'category': 'cold-corporate',
                'subject': COLD_CORPORATE_SUBJECT,
                'body': COLD_CORPORATE_BODY,
                'required_variables': 'nombre,empresa,senal_detectada,firma_comercial',
                'is_active': 1,
                'notes': 'Para corporaciones grandes que NO van a comprar back office completo pero pueden necesitar apoyo en proyectos puntuales en Iberia. Tono más senior, menos comercial, ofreciendo ejecución práctica vs consultora generalista.',
                'created_at': now,
                'updated_at': now,
            },
        ],
    )


def downgrade():
    op.drop_index('ix_emails_sent_template_id', table_name='emails_sent')
    op.drop_index('ix_emails_sent_contact_id', table_name='emails_sent')
    op.drop_index('ix_emails_sent_account_id', table_name='emails_sent')
    op.drop_table('emails_sent')
    op.drop_index('ix_email_templates_is_active', table_name='email_templates')
    op.drop_index('ix_email_templates_category', table_name='email_templates')
    op.drop_table('email_templates')
