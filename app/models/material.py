from sqlalchemy import Column, String, Text, Integer, LargeBinary, ForeignKey
from datetime import datetime, timezone
from app.database import Base, UTCDateTime


class MaterialDocument(Base):
    """
    Tabla: material_documents
    Repositorio de material comercial (decks, propuestas, guías).
    Regla: una sola versión activa por name_slug; al subir nueva, las anteriores pasan a 'retired'.
    """
    __tablename__ = "material_documents"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    name_slug = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    usage_note = Column(Text, nullable=True)

    file_name = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_data = Column(LargeBinary, nullable=False)

    status = Column(String, nullable=False, default="active", index=True)  # active | retired

    uploaded_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(UTCDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))

    retired_at = Column(UTCDateTime(), nullable=True)
    retired_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
