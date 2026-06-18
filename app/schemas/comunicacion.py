from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class DesarrolloResponse(BaseModel):
    id: str
    publicacion_id: str
    titulo_crudo: str
    tipo: Optional[str] = None
    fecha: Optional[str] = None
    observaciones: Optional[str] = None
    modulo: Optional[str] = None
    origen: Optional[str] = None
    proyecto: Optional[str] = None
    norma: Optional[str] = None
    mantenimiento: bool = False
    relacionado_con: Optional[str] = None
    canales: Optional[str] = None
    incluir: bool = True
    orden: Optional[int] = None

    class Config:
        from_attributes = True


class DesarrolloUpdate(BaseModel):
    norma: Optional[str] = None
    mantenimiento: Optional[bool] = None
    relacionado_con: Optional[str] = None
    canales: Optional[str] = None
    incluir: Optional[bool] = None
    titulo_crudo: Optional[str] = None
    observaciones: Optional[str] = None
    orden: Optional[int] = None


class PublicacionResponse(BaseModel):
    id: str
    version_erp: Optional[str] = None
    fecha_ingesta: datetime
    estado: str
    n_desarrollos: int = 0

    class Config:
        from_attributes = True


class PublicacionListResponse(BaseModel):
    publicaciones: List[PublicacionResponse]
    total: int


class PublicacionDetailResponse(BaseModel):
    publicacion: PublicacionResponse
    desarrollos: List[DesarrolloResponse]


class IngestaResponse(BaseModel):
    publicacion_id: str
    n_desarrollos: int
    version_erp: Optional[str] = None


class SalidaCanalResponse(BaseModel):
    id: str
    publicacion_id: str
    canal: str
    contenido_generado: Optional[Any] = None
    contenido_editado: Optional[Any] = None
    estado: str
    meta: Optional[Any] = None
    fecha_publicacion: Optional[datetime] = None

    class Config:
        from_attributes = True


class SalidaCanalUpdate(BaseModel):
    contenido_editado: Optional[Any] = None
    meta: Optional[Any] = None
    estado: Optional[str] = None
