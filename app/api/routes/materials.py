"""
Endpoints for commercial material repository.
Admin sube/sustituye versiones; comerciales solo descargan los documentos activos.
Regla critica: solo una version activa por name_slug — al subir nueva, las anteriores pasan a 'retired'.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
import re
import logging

from app.database import get_db
from app.models.user import User
from app.models.material import MaterialDocument
from app.schemas.material import MaterialResponse, MaterialListResponse, MaterialUpdate
from app.utils.auth import get_current_user_from_cookie
from app.utils.audit import generate_id, get_utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/materials", tags=["Materials"])
templates = Jinja2Templates(directory="app/templates")

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def _slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[áàä]", "a", s)
    s = re.sub(r"[éèë]", "e", s)
    s = re.sub(r"[íìï]", "i", s)
    s = re.sub(r"[óòö]", "o", s)
    s = re.sub(r"[úùü]", "u", s)
    s = re.sub(r"ñ", "n", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "material"


def _to_response(m: MaterialDocument, user_name: Optional[str] = None) -> MaterialResponse:
    return MaterialResponse(
        id=m.id,
        name=m.name,
        name_slug=m.name_slug,
        version=m.version,
        usage_note=m.usage_note,
        file_name=m.file_name,
        mime_type=m.mime_type,
        file_size=m.file_size,
        status=m.status,
        uploaded_by_user_id=m.uploaded_by_user_id,
        uploaded_by_name=user_name,
        uploaded_at=m.uploaded_at,
        retired_at=m.retired_at,
    )


def _attach_user_names(db: Session, items):
    user_ids = {i.uploaded_by_user_id for i in items if i.uploaded_by_user_id}
    if not user_ids:
        return {}
    return {u.id: u.name for u in db.query(User).filter(User.id.in_(user_ids)).all()}


@router.get("/page", response_class=HTMLResponse)
async def materials_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
):
    return templates.TemplateResponse("materials.html", {"request": request})


@router.get("", response_model=MaterialListResponse)
def list_active_materials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Cualquier usuario autenticado ve los documentos activos."""
    items = (
        db.query(MaterialDocument)
        .filter(MaterialDocument.status == "active")
        .order_by(MaterialDocument.name.asc())
        .all()
    )
    names = _attach_user_names(db, items)
    return MaterialListResponse(
        materials=[_to_response(m, names.get(m.uploaded_by_user_id)) for m in items],
        total=len(items),
    )


@router.get("/admin", response_model=MaterialListResponse)
def list_all_materials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
    include_retired: bool = True,
):
    """Admin: ve todos los documentos (activos + retirados)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    q = db.query(MaterialDocument)
    if not include_retired:
        q = q.filter(MaterialDocument.status == "active")
    items = q.order_by(MaterialDocument.name_slug.asc(), desc(MaterialDocument.uploaded_at)).all()
    names = _attach_user_names(db, items)
    return MaterialListResponse(
        materials=[_to_response(m, names.get(m.uploaded_by_user_id)) for m in items],
        total=len(items),
    )


@router.post("", response_model=MaterialResponse, status_code=201)
async def upload_material(
    file: UploadFile = File(...),
    name: str = Form(...),
    version: str = Form(...),
    usage_note: str = Form(""),
    name_slug: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """
    Sube un nuevo documento o nueva version de uno existente.
    Si name_slug coincide con un material activo, ese pasa a 'retired' automaticamente.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin puede subir material")

    name = (name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    version = (version or "").strip()
    if not version:
        raise HTTPException(status_code=400, detail="La version es obligatoria")
    slug = name_slug.strip() if name_slug else _slugify(name)

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="El archivo esta vacio")
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"Archivo demasiado grande (max {MAX_FILE_SIZE // (1024*1024)} MB)")

    now = get_utc_now()

    # Retirar versiones anteriores activas con el mismo slug
    previous_active = db.query(MaterialDocument).filter(
        MaterialDocument.name_slug == slug,
        MaterialDocument.status == "active",
    ).all()
    for prev in previous_active:
        prev.status = "retired"
        prev.retired_at = now
        prev.retired_by_user_id = current_user.id

    m = MaterialDocument(
        id=generate_id(),
        name=name,
        name_slug=slug,
        version=version,
        usage_note=(usage_note or "").strip() or None,
        file_name=file.filename or "documento",
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(contents),
        file_data=contents,
        status="active",
        uploaded_by_user_id=current_user.id,
        uploaded_at=now,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    logger.info(f"[materials] upload slug={slug} version={version} size={len(contents)} retired_prev={len(previous_active)}")
    return _to_response(m, current_user.name)


@router.get("/{material_id}/download")
def download_material(
    material_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Descarga del fichero. Los comerciales solo pueden bajar 'active'; admin tambien retirados."""
    m = db.query(MaterialDocument).filter(MaterialDocument.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="No encontrado")
    if m.status != "active" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Este material esta retirado")
    safe_name = m.file_name.replace('"', '')
    return Response(
        content=m.file_data,
        media_type=m.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


@router.patch("/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: str,
    payload: MaterialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    m = db.query(MaterialDocument).filter(MaterialDocument.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="No encontrado")
    if payload.name is not None:
        m.name = payload.name.strip()
    if payload.usage_note is not None:
        m.usage_note = payload.usage_note.strip() or None
    if payload.version is not None:
        m.version = payload.version.strip()
    db.commit()
    db.refresh(m)
    user_name = db.query(User.name).filter(User.id == m.uploaded_by_user_id).scalar() if m.uploaded_by_user_id else None
    return _to_response(m, user_name)


@router.post("/{material_id}/retire", response_model=MaterialResponse)
def retire_material(
    material_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    m = db.query(MaterialDocument).filter(MaterialDocument.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="No encontrado")
    m.status = "retired"
    m.retired_at = get_utc_now()
    m.retired_by_user_id = current_user.id
    db.commit()
    db.refresh(m)
    user_name = db.query(User.name).filter(User.id == m.uploaded_by_user_id).scalar() if m.uploaded_by_user_id else None
    return _to_response(m, user_name)


@router.post("/{material_id}/restore", response_model=MaterialResponse)
def restore_material(
    material_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Reactiva un material retirado. Si hay otro activo con el mismo slug, ese pasa a retirado."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    m = db.query(MaterialDocument).filter(MaterialDocument.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="No encontrado")
    now = get_utc_now()
    others = db.query(MaterialDocument).filter(
        MaterialDocument.name_slug == m.name_slug,
        MaterialDocument.status == "active",
        MaterialDocument.id != m.id,
    ).all()
    for o in others:
        o.status = "retired"
        o.retired_at = now
        o.retired_by_user_id = current_user.id
    m.status = "active"
    m.retired_at = None
    m.retired_by_user_id = None
    db.commit()
    db.refresh(m)
    user_name = db.query(User.name).filter(User.id == m.uploaded_by_user_id).scalar() if m.uploaded_by_user_id else None
    return _to_response(m, user_name)


@router.delete("/{material_id}", status_code=204)
def delete_material(
    material_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Hard delete — solo para errores de upload. Para retirar por flujo normal usar /retire."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    m = db.query(MaterialDocument).filter(MaterialDocument.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(m)
    db.commit()
    return Response(status_code=204)
