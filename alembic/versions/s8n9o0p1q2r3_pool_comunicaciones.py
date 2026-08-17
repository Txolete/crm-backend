"""pool de desarrollos: estado_comunicacion + Comunicacion desacoplada de Publicacion

Revision ID: s8n9o0p1q2r3
Revises: r7m8n9o0p1q2
Create Date: 2026-08-17

Antes: 1 ingesta (Publicacion) = 1 comunicacion (SalidaCanal), 1:1. Un desarrollo solo
se podia comunicar junto a los de su misma ingesta.

Ahora: los desarrollos viven en un "pool" con su propio estado_comunicacion
(pendiente/comunicado/no_comunicar), independiente de en que ingesta llegaron. Una
Comunicacion agrupa los desarrollos elegidos del pool (tabla puente
comunicacion_desarrollos), sean de la ingesta que sean.

Migra los datos existentes de salidas_canal (sin envios reales todavia, confirmado
con el socio) a la nueva forma antes de borrar la tabla vieja.
"""
from alembic import op
import sqlalchemy as sa
import uuid

revision = 's8n9o0p1q2r3'
down_revision = 'r7m8n9o0p1q2'
branch_labels = None
depends_on = None


def upgrade():
    # --- estado_comunicacion en desarrollos (reemplaza a incluir) ---
    op.add_column('desarrollos', sa.Column('estado_comunicacion', sa.String(), nullable=False, server_default='pendiente'))
    op.execute("UPDATE desarrollos SET estado_comunicacion = 'no_comunicar' WHERE mantenimiento = 1")

    # --- nuevas tablas ---
    op.create_table(
        'comunicaciones',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('canal', sa.String(), nullable=False, server_default='correo'),
        sa.Column('nombre', sa.String(), nullable=True),
        sa.Column('contenido_generado', sa.Text(), nullable=True),
        sa.Column('contenido_editado', sa.Text(), nullable=True),
        sa.Column('estado', sa.String(), nullable=False, server_default='borrador'),
        sa.Column('meta', sa.Text(), nullable=True),
        sa.Column('fecha_publicacion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        'comunicacion_desarrollos',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('comunicacion_id', sa.String(), sa.ForeignKey('comunicaciones.id'), nullable=False),
        sa.Column('desarrollo_id', sa.String(), sa.ForeignKey('desarrollos.id'), nullable=False),
        sa.Column('orden', sa.Integer(), nullable=True),
    )
    op.create_index('ix_comunicacion_desarrollos_comunicacion_id', 'comunicacion_desarrollos', ['comunicacion_id'])
    op.create_index('ix_comunicacion_desarrollos_desarrollo_id', 'comunicacion_desarrollos', ['desarrollo_id'])

    # --- migrar filas existentes de salidas_canal (borradores/pruebas, sin envios reales) ---
    bind = op.get_bind()
    salidas = bind.execute(sa.text(
        "SELECT id, publicacion_id, canal, contenido_generado, contenido_editado, estado, "
        "meta, fecha_publicacion, created_at, updated_at FROM salidas_canal"
    )).fetchall()
    for s in salidas:
        bind.execute(sa.text(
            "INSERT INTO comunicaciones (id, canal, nombre, contenido_generado, contenido_editado, "
            "estado, meta, fecha_publicacion, created_at, updated_at) "
            "VALUES (:id, :canal, NULL, :cg, :ce, :estado, :meta, :fp, :ca, :ua)"
        ), {
            "id": s.id, "canal": s.canal, "cg": s.contenido_generado, "ce": s.contenido_editado,
            "estado": s.estado, "meta": s.meta, "fp": s.fecha_publicacion,
            "ca": s.created_at, "ua": s.updated_at,
        })
        desarrollos = bind.execute(sa.text(
            "SELECT id, orden FROM desarrollos WHERE publicacion_id = :pid"
        ), {"pid": s.publicacion_id}).fetchall()
        for d in desarrollos:
            bind.execute(sa.text(
                "INSERT INTO comunicacion_desarrollos (id, comunicacion_id, desarrollo_id, orden) "
                "VALUES (:id, :cid, :did, :orden)"
            ), {"id": str(uuid.uuid4()), "cid": s.id, "did": d.id, "orden": d.orden})
            # si la comunicacion ya estaba publicada, el desarrollo pasa a comunicado
            if s.estado == "publicado":
                bind.execute(sa.text(
                    "UPDATE desarrollos SET estado_comunicacion = 'comunicado' WHERE id = :did"
                ), {"did": d.id})

    op.drop_table('salidas_canal')
    op.drop_column('desarrollos', 'incluir')


def downgrade():
    op.add_column('desarrollos', sa.Column('incluir', sa.Integer(), nullable=False, server_default='1'))
    op.execute("UPDATE desarrollos SET incluir = 0 WHERE estado_comunicacion = 'no_comunicar'")

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

    # Best-effort: una comunicacion puede agrupar desarrollos de varias ingestas, algo
    # que salidas_canal no puede representar (1 publicacion_id). Se usa la publicacion
    # del primer desarrollo vinculado; si una comunicacion no tiene desarrollos, se descarta.
    bind = op.get_bind()
    comunicaciones = bind.execute(sa.text(
        "SELECT id, canal, contenido_generado, contenido_editado, estado, meta, "
        "fecha_publicacion, created_at, updated_at FROM comunicaciones"
    )).fetchall()
    for c in comunicaciones:
        primero = bind.execute(sa.text(
            "SELECT d.publicacion_id FROM comunicacion_desarrollos cd "
            "JOIN desarrollos d ON d.id = cd.desarrollo_id "
            "WHERE cd.comunicacion_id = :cid ORDER BY cd.orden ASC LIMIT 1"
        ), {"cid": c.id}).fetchone()
        if not primero:
            continue
        bind.execute(sa.text(
            "INSERT INTO salidas_canal (id, publicacion_id, canal, contenido_generado, "
            "contenido_editado, estado, meta, fecha_publicacion, created_at, updated_at) "
            "VALUES (:id, :pid, :canal, :cg, :ce, :estado, :meta, :fp, :ca, :ua)"
        ), {
            "id": c.id, "pid": primero.publicacion_id, "canal": c.canal,
            "cg": c.contenido_generado, "ce": c.contenido_editado, "estado": c.estado,
            "meta": c.meta, "fp": c.fecha_publicacion, "ca": c.created_at, "ua": c.updated_at,
        })

    op.drop_index('ix_comunicacion_desarrollos_desarrollo_id', table_name='comunicacion_desarrollos')
    op.drop_index('ix_comunicacion_desarrollos_comunicacion_id', table_name='comunicacion_desarrollos')
    op.drop_table('comunicacion_desarrollos')
    op.drop_table('comunicaciones')
    op.drop_column('desarrollos', 'estado_comunicacion')
