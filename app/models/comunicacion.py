from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base, UTCDateTime


class Publicacion(Base):
    """
    Tabla: publicaciones
    Registro de auditoría de una ingesta de Excel de BOMP: cuándo se subió, con qué
    versión/release y cuántos desarrollos trajo. NO representa una comunicación: los
    desarrollos que entran aquí pasan al pool y se comunican de forma independiente
    (posiblemente junto a desarrollos de otras ingestas, ver Comunicacion).
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

    Vive en el "pool": pertenece a la ingesta (publicacion_id) en la que llegó por
    auditoría/trazabilidad, pero su estado_comunicacion es independiente de eso — se
    puede comunicar junto a desarrollos de otras ingestas en una misma Comunicacion.
    """
    __tablename__ = "desarrollos"

    id = Column(String, primary_key=True)
    publicacion_id = Column(String, ForeignKey("publicaciones.id"), nullable=False, index=True)

    # ID original del desarrollo en BOMP (columna "ID" del Excel). Nullable porque puede
    # haber desarrollos creados a mano sin origen en BOMP. Unique para no duplicar al
    # reimportar el mismo desarrollo en una publicación distinta.
    bomp_id = Column(Integer, nullable=True, unique=True, index=True)

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
    # 0/1 → desarrollo interno/técnico, resumen sobrio, no titular. Los marcados como
    # mantenimiento entran en el pool con estado_comunicacion="no_comunicar" por defecto;
    # el socio puede reactivarlos manualmente uno a uno desde la ficha.
    mantenimiento = Column(Integer, nullable=False, default=0)
    # Self-FK al desarrollo "padre" del que es evolución/consolidación. Se resuelve
    # automáticamente en el import por bomp_id (columna "ID del desarrollo relacionado").
    relacionado_con = Column(String, ForeignKey("desarrollos.id"), nullable=True)
    canales = Column(String, nullable=True)             # CSV: "correo,linkedin"

    # Estado del desarrollo en el pool de comunicación, INDEPENDIENTE de la ingesta en la
    # que llegó: pendiente (candidato, aún no se ha decidido) | comunicado (ya salió en
    # alguna Comunicacion enviada) | no_comunicar (el socio ha decidido que no se cuenta,
    # p.ej. mantenimiento o trabajo puramente interno). Se pasa a "comunicado" automatico
    # al marcar una Comunicacion como enviada (real o manual).
    estado_comunicacion = Column(String, nullable=False, default="pendiente")

    orden = Column(Integer, nullable=True)

    desarrollo_relacionado = relationship(
        "Desarrollo", remote_side=[id], foreign_keys=[relacionado_con],
        backref="desarrollos_posteriores",
    )


class ComunicacionPrompt(Base):
    """
    Tabla: comunicacion_prompts
    Versiones del prompt del adaptador de correo. El socio puede guardar varias
    y activar una. hero_level controla cuánta épica/hero mete (1 menos, 3 más).
    calibracion son ejemplos extra (bien/meh/mal) que se aprenden desde la curación.
    """
    __tablename__ = "comunicacion_prompts"

    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False)
    canal = Column(String, nullable=False, default="correo")
    prompt_text = Column(Text, nullable=True)   # si null/vacío, usa el prompt por defecto del código
    hero_level = Column(Integer, nullable=False, default=2)  # 1=menos, 2=medio, 3=más
    calibracion = Column(Text, nullable=True)   # ejemplos extra acumulados (feedback)
    activa = Column(Integer, nullable=False, default=0)
    created_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Comunicacion(Base):
    """
    Tabla: comunicaciones
    Una comunicación real (borrador o ya enviada) a un canal. NO está ligada a una
    Publicacion/ingesta concreta: agrupa los desarrollos que se han elegido del pool
    (ver ComunicacionDesarrollo), sea cual sea la ingesta de la que vinieron.
    """
    __tablename__ = "comunicaciones"

    id = Column(String, primary_key=True)
    canal = Column(String, nullable=False, default="correo")  # correo | linkedin | ...
    nombre = Column(String, nullable=True)  # etiqueta libre para identificarla en el historial

    contenido_generado = Column(Text, nullable=True)  # JSON salida de la IA
    contenido_editado = Column(Text, nullable=True)   # JSON tras edición del socio
    # borrador (creada) | adaptado (la IA ya generó contenido) | publicado (enviada, real o manual)
    estado = Column(String, nullable=False, default="borrador")

    # meta JSON: correo → { asunto, destinatarios_to[], _cc[], _bcc[], saludo, firma }
    meta = Column(Text, nullable=True)

    fecha_publicacion = Column(UTCDateTime(), nullable=True)
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ComunicacionDesarrollo(Base):
    """
    Tabla: comunicacion_desarrollos
    Tabla puente: qué desarrollos entran en qué comunicación. Es lo que permite que una
    misma comunicación agrupe desarrollos de ingestas (Publicacion) distintas — el "pool".
    """
    __tablename__ = "comunicacion_desarrollos"

    id = Column(String, primary_key=True)
    comunicacion_id = Column(String, ForeignKey("comunicaciones.id"), nullable=False, index=True)
    desarrollo_id = Column(String, ForeignKey("desarrollos.id"), nullable=False, index=True)
    orden = Column(Integer, nullable=True)
