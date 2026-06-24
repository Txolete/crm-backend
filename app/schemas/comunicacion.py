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


class PromptResponse(BaseModel):
    id: str
    nombre: str
    canal: str
    prompt_text: Optional[str] = None
    hero_level: int = 2
    calibracion: Optional[str] = None
    activa: bool = False

    class Config:
        from_attributes = True


class PromptListResponse(BaseModel):
    prompts: List[PromptResponse]
    default_prompt: str   # el prompt por defecto del código, para referencia


class PromptCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=120)
    prompt_text: Optional[str] = None
    hero_level: int = Field(2, ge=1, le=3)
    calibracion: Optional[str] = None


class PromptUpdate(BaseModel):
    nombre: Optional[str] = None
    prompt_text: Optional[str] = None
    hero_level: Optional[int] = Field(None, ge=1, le=3)
    calibracion: Optional[str] = None


class FeedbackItem(BaseModel):
    titulo: Optional[str] = None
    cuerpo: Optional[str] = None
    veredicto: str = Field(..., pattern="^(bien|meh|mal)$")
    nota: Optional[str] = None
