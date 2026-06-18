from sqlalchemy import Column, String, Text, Integer, ForeignKey
from datetime import datetime, timezone
from app.database import Base, UTCDateTime


class Publicacion(Base):
    """
    Tabla: publicaciones
    Una tanda de desarrollos curada junta (batch agnóstico de canal).
    """
    __tablename__ = "publicaciones"

    id = Column(String, primary_key=True)
    version_erp = Column(String, nullable=True)
    fecha_ingesta = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
    estado = Column(String, nullable=False, default="borrador")  # borrador | curada
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)


class Desarrollo(Base):
    """
    Tabla: desarrollos
    Una fila por desarrollo, en crudo desde el ERP (Excel en Fase 1).
    Se guarda el crudo siempre, aunque luego se adapte.
    """
    __tablename__ = "desarrollos"

    id = Column(String, primary_key=True)
    publicacion_id = Column(String, ForeignKey("publicaciones.id"), nullable=False, index=True)

    # Campos en crudo del ERP (Excel: Actualización, Tipo, Fecha, Observaciones, Módulo, Origen, Proyecto)
    titulo_crudo = Column(String, nullable=False)
    tipo = Column(String, nullable=True)         # Nueva funcionalidad | Mejora... | Adaptación regulatoria | Corrección de errores/bugs
    fecha = Column(String, nullable=True)        # fecha del ERP (string, tal cual)
    observaciones = Column(Text, nullable=True)  # texto técnico en crudo a adaptar
    modulo = Column(String, nullable=True)
    origen = Column(String, nullable=True)       # Adm | Extranet | Ambas
    proyecto = Column(String, nullable=True)     # BOMP 1 / BOMP 2 / API / GAS...

    # Campos que se rellenan en el CRM
    norma = Column(String, nullable=True)               # solo si tipo = Adaptación regulatoria
    mantenimiento = Column(Integer, nullable=False, default=0)  # 0/1 → resumen sobrio, no titular
    relacionado_con = Column(String, nullable=True)     # enlaza evolutivos para consolidar
    canales = Column(String, nullable=True)             # CSV: "correo,linkedin"
    incluir = Column(Integer, nullable=False, default=1)  # el socio marca si entra en la comunicación

    orden = Column(Integer, nullable=True)


class SalidaCanal(Base):
    """
    Tabla: salidas_canal
    Una fila por combinación publicación × canal. Aquí vive lo específico del canal.
    Esta tabla es la que hace el hub extensible.
    """
    __tablename__ = "salidas_canal"

    id = Column(String, primary_key=True)
    publicacion_id = Column(String, ForeignKey("publicaciones.id"), nullable=False, index=True)
    canal = Column(String, nullable=False, default="correo")  # correo | linkedin | ...

    contenido_generado = Column(Text, nullable=True)  # JSON salida de la IA
    contenido_editado = Column(Text, nullable=True)   # JSON tras edición del socio
    estado = Column(String, nullable=False, default="borrador")  # borrador | adaptado | revisado | publicado

    # meta JSON: correo → { asunto, destinatarios_to[], _cc[], _bcc[], _extra[], html_final }
    meta = Column(Text, nullable=True)

    fecha_publicacion = Column(UTCDateTime(), nullable=True)
    created_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
