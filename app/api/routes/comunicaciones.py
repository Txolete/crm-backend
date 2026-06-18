"""
Hub de comunicación — canal CORREO (MVP).
Ingesta de novedades del ERP (Excel), adaptación con IA, maquetación HTML.
Solo admin.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional
import io
import json
import logging

from app.database import get_db
from app.models.user import User
from app.models.comunicacion import Publicacion, Desarrollo, SalidaCanal
from app.schemas.comunicacion import (
    DesarrolloResponse, DesarrolloUpdate,
    PublicacionResponse, PublicacionListResponse, PublicacionDetailResponse,
    IngestaResponse, SalidaCanalResponse, SalidaCanalUpdate,
)
from app.utils.auth import get_current_user_from_cookie
from app.utils.audit import generate_id, get_utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/comunicaciones", tags=["Comunicaciones"])
templates = Jinja2Templates(directory="app/templates")


def _require_admin(current_user: User):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")


# Mapeo flexible de cabeceras del Excel -> campo interno
COLUMN_MAP = {
    "actualización": "titulo_crudo",
    "actualizacion": "titulo_crudo",
    "tipo": "tipo",
    "fecha": "fecha",
    "observaciones": "observaciones",
    "módulo": "modulo",
    "modulo": "modulo",
    "origen": "origen",
    "proyecto": "proyecto",
}


def _norm_header(h) -> str:
    return str(h or "").strip().lower()


@router.get("/page", response_class=HTMLResponse)
async def comunicaciones_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
):
    _require_admin(current_user)
    return templates.TemplateResponse("comunicaciones.html", {"request": request})


@router.post("/ingesta-excel", response_model=IngestaResponse, status_code=201)
async def ingesta_excel(
    file: UploadFile = File(...),
    version_erp: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """
    Sube el Excel de novedades del ERP y crea una Publicacion + N Desarrollos en crudo.
    Columnas esperadas: Actualización, Tipo, Fecha, Observaciones, Módulo, Origen, Proyecto.
    """
    _require_admin(current_user)

    from openpyxl import load_workbook
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    try:
        wb = load_workbook(io.BytesIO(contents), read_only=True, data_only=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el Excel: {e}")

    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise HTTPException(status_code=400, detail="El Excel no tiene filas")

    # Mapear cabecera
    header = rows[0]
    col_idx = {}
    for i, h in enumerate(header):
        key = COLUMN_MAP.get(_norm_header(h))
        if key:
            col_idx[key] = i
    if "titulo_crudo" not in col_idx:
        raise HTTPException(
            status_code=400,
            detail="No se encontró la columna 'Actualización'. Revisa la cabecera del Excel.",
        )

    now = get_utc_now()
    pub = Publicacion(
        id=generate_id(),
        version_erp=(version_erp or "").strip() or None,
        fecha_ingesta=now,
        estado="borrador",
        created_by_user_id=current_user.id,
    )
    db.add(pub)
    db.flush()

    n = 0
    for ridx, row in enumerate(rows[1:], start=1):
        def cell(field):
            idx = col_idx.get(field)
            if idx is None or idx >= len(row):
                return None
            val = row[idx]
            return val

        titulo = cell("titulo_crudo")
        if titulo is None or str(titulo).strip() == "":
            continue  # saltar filas vacías

        fecha_val = cell("fecha")
        if fecha_val is not None and hasattr(fecha_val, "strftime"):
            fecha_val = fecha_val.strftime("%Y-%m-%d")

        d = Desarrollo(
            id=generate_id(),
            publicacion_id=pub.id,
            titulo_crudo=str(titulo).strip(),
            tipo=(str(cell("tipo")).strip() if cell("tipo") else None),
            fecha=(str(fecha_val).strip() if fecha_val else None),
            observaciones=(str(cell("observaciones")).strip() if cell("observaciones") else None),
            modulo=(str(cell("modulo")).strip() if cell("modulo") else None),
            origen=(str(cell("origen")).strip() if cell("origen") else None),
            proyecto=(str(cell("proyecto")).strip() if cell("proyecto") else None),
            mantenimiento=0,
            canales="correo",   # por defecto candidato a correo; el socio ajusta
            incluir=1,
            orden=ridx,
        )
        db.add(d)
        n += 1

    db.commit()
    logger.info(f"[comunicaciones] ingesta excel pub={pub.id} desarrollos={n}")
    return IngestaResponse(publicacion_id=pub.id, n_desarrollos=n, version_erp=pub.version_erp)


@router.get("", response_model=PublicacionListResponse)
def list_publicaciones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    _require_admin(current_user)
    pubs = db.query(Publicacion).order_by(desc(Publicacion.fecha_ingesta)).all()
    counts = dict(
        db.query(Desarrollo.publicacion_id, func.count(Desarrollo.id))
        .group_by(Desarrollo.publicacion_id).all()
    )
    return PublicacionListResponse(
        publicaciones=[
            PublicacionResponse(
                id=p.id, version_erp=p.version_erp, fecha_ingesta=p.fecha_ingesta,
                estado=p.estado, n_desarrollos=counts.get(p.id, 0),
            ) for p in pubs
        ],
        total=len(pubs),
    )


@router.get("/{publicacion_id}", response_model=PublicacionDetailResponse)
def get_publicacion(
    publicacion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    _require_admin(current_user)
    p = db.query(Publicacion).filter(Publicacion.id == publicacion_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")
    desarrollos = (
        db.query(Desarrollo)
        .filter(Desarrollo.publicacion_id == publicacion_id)
        .order_by(Desarrollo.orden.asc())
        .all()
    )
    n = len(desarrollos)
    return PublicacionDetailResponse(
        publicacion=PublicacionResponse(
            id=p.id, version_erp=p.version_erp, fecha_ingesta=p.fecha_ingesta,
            estado=p.estado, n_desarrollos=n,
        ),
        desarrollos=[
            DesarrolloResponse(
                id=d.id, publicacion_id=d.publicacion_id, titulo_crudo=d.titulo_crudo,
                tipo=d.tipo, fecha=d.fecha, observaciones=d.observaciones, modulo=d.modulo,
                origen=d.origen, proyecto=d.proyecto, norma=d.norma,
                mantenimiento=bool(d.mantenimiento), relacionado_con=d.relacionado_con,
                canales=d.canales, incluir=bool(d.incluir), orden=d.orden,
            ) for d in desarrollos
        ],
    )


@router.patch("/desarrollos/{desarrollo_id}", response_model=DesarrolloResponse)
def update_desarrollo(
    desarrollo_id: str,
    payload: DesarrolloUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    _require_admin(current_user)
    d = db.query(Desarrollo).filter(Desarrollo.id == desarrollo_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Desarrollo no encontrado")
    if payload.norma is not None: d.norma = payload.norma.strip() or None
    if payload.mantenimiento is not None: d.mantenimiento = 1 if payload.mantenimiento else 0
    if payload.relacionado_con is not None: d.relacionado_con = payload.relacionado_con.strip() or None
    if payload.canales is not None: d.canales = payload.canales.strip() or None
    if payload.incluir is not None: d.incluir = 1 if payload.incluir else 0
    if payload.titulo_crudo is not None: d.titulo_crudo = payload.titulo_crudo.strip()
    if payload.observaciones is not None: d.observaciones = payload.observaciones
    if payload.orden is not None: d.orden = payload.orden
    db.commit()
    db.refresh(d)
    return DesarrolloResponse(
        id=d.id, publicacion_id=d.publicacion_id, titulo_crudo=d.titulo_crudo,
        tipo=d.tipo, fecha=d.fecha, observaciones=d.observaciones, modulo=d.modulo,
        origen=d.origen, proyecto=d.proyecto, norma=d.norma,
        mantenimiento=bool(d.mantenimiento), relacionado_con=d.relacionado_con,
        canales=d.canales, incluir=bool(d.incluir), orden=d.orden,
    )


@router.delete("/{publicacion_id}", status_code=204)
def delete_publicacion(
    publicacion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    _require_admin(current_user)
    p = db.query(Publicacion).filter(Publicacion.id == publicacion_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="No encontrada")
    db.query(SalidaCanal).filter(SalidaCanal.publicacion_id == publicacion_id).delete()
    db.query(Desarrollo).filter(Desarrollo.publicacion_id == publicacion_id).delete()
    db.delete(p)
    db.commit()
    return None
