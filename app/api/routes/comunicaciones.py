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
from app.models.comunicacion import Publicacion, Desarrollo, SalidaCanal, ComunicacionPrompt
from app.schemas.comunicacion import (
    DesarrolloResponse, DesarrolloUpdate,
    PublicacionResponse, PublicacionListResponse, PublicacionDetailResponse,
    IngestaResponse, SalidaCanalResponse, SalidaCanalUpdate,
    PromptResponse, PromptListResponse, PromptCreate, PromptUpdate, FeedbackItem,
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


def _desarrollo_to_ai_dict(d: Desarrollo) -> dict:
    return {
        "id": d.id,
        "titulo_crudo": d.titulo_crudo,
        "tipo": d.tipo,
        "modulo": d.modulo,
        "proyecto": d.proyecto,
        "origen": d.origen,
        "observaciones": d.observaciones,
        "mantenimiento": bool(d.mantenimiento),
        "relacionado_con": d.relacionado_con,
        "norma": d.norma,
    }


def _get_or_create_salida(db: Session, publicacion_id: str, canal: str = "correo") -> SalidaCanal:
    s = (
        db.query(SalidaCanal)
        .filter(SalidaCanal.publicacion_id == publicacion_id, SalidaCanal.canal == canal)
        .first()
    )
    if not s:
        now = get_utc_now()
        s = SalidaCanal(
            id=generate_id(), publicacion_id=publicacion_id, canal=canal,
            estado="borrador", created_at=now, updated_at=now,
        )
        db.add(s)
        db.flush()
    return s


def _salida_response(s: SalidaCanal) -> SalidaCanalResponse:
    def _loads(v):
        if not v:
            return None
        try:
            return json.loads(v)
        except Exception:
            return None
    return SalidaCanalResponse(
        id=s.id, publicacion_id=s.publicacion_id, canal=s.canal,
        contenido_generado=_loads(s.contenido_generado),
        contenido_editado=_loads(s.contenido_editado),
        estado=s.estado, meta=_loads(s.meta),
        fecha_publicacion=s.fecha_publicacion,
    )


@router.post("/{publicacion_id}/adaptar-correo", response_model=SalidaCanalResponse)
def adaptar_correo_endpoint(
    publicacion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """
    Llama a la IA con los desarrollos marcados para correo (incluir=1 y canal 'correo')
    y guarda el JSON adaptado en la SalidaCanal.
    """
    _require_admin(current_user)
    p = db.query(Publicacion).filter(Publicacion.id == publicacion_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Publicación no encontrada")

    desarrollos = (
        db.query(Desarrollo)
        .filter(Desarrollo.publicacion_id == publicacion_id, Desarrollo.incluir == 1)
        .order_by(Desarrollo.orden.asc())
        .all()
    )
    # Filtrar los que van al canal correo
    para_correo = [d for d in desarrollos if not d.canales or "correo" in (d.canales or "")]
    if not para_correo:
        raise HTTPException(status_code=400, detail="No hay desarrollos marcados para el canal correo")

    from app.utils.comunicaciones_ai import adaptar_correo, build_system_prompt
    # Cargar prompt activo (si existe), aplicar hero level + calibracion
    activa = (
        db.query(ComunicacionPrompt)
        .filter(ComunicacionPrompt.canal == "correo", ComunicacionPrompt.activa == 1)
        .first()
    )
    sys_prompt = build_system_prompt(
        prompt_text=(activa.prompt_text if activa else None),
        hero_level=(activa.hero_level if activa else 2),
        calibracion_extra=(activa.calibracion if activa else None),
    )
    try:
        contenido = adaptar_correo([_desarrollo_to_ai_dict(d) for d in para_correo], system_prompt=sys_prompt)
    except Exception as e:
        logger.error(f"[comunicaciones] adaptar IA error: {e}")
        raise HTTPException(status_code=502, detail=f"Error en la IA: {e}")

    s = _get_or_create_salida(db, publicacion_id, "correo")
    s.contenido_generado = json.dumps(contenido, ensure_ascii=False)
    # Inicializar contenido_editado con lo generado si está vacío (para que el socio edite encima)
    if not s.contenido_editado:
        s.contenido_editado = s.contenido_generado
    s.estado = "adaptado"
    # Sembrar el asunto en meta si no existe
    meta = {}
    if s.meta:
        try:
            meta = json.loads(s.meta)
        except Exception:
            meta = {}
    meta.setdefault("asunto", contenido.get("asunto", "Novedades BOMP"))
    meta.setdefault("destinatarios_to", [])
    meta.setdefault("destinatarios_cc", [])
    meta.setdefault("destinatarios_bcc", [])
    s.meta = json.dumps(meta, ensure_ascii=False)
    s.updated_at = get_utc_now()
    p.estado = "curada"
    db.commit()
    db.refresh(s)
    logger.info(f"[comunicaciones] adaptado correo pub={publicacion_id} items={len(contenido.get('items', []))}")
    return _salida_response(s)


@router.get("/{publicacion_id}/salida/{canal}", response_model=SalidaCanalResponse)
def get_salida(
    publicacion_id: str,
    canal: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    _require_admin(current_user)
    s = (
        db.query(SalidaCanal)
        .filter(SalidaCanal.publicacion_id == publicacion_id, SalidaCanal.canal == canal)
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="Aún no se ha adaptado este canal")
    return _salida_response(s)


@router.patch("/salida/{salida_id}", response_model=SalidaCanalResponse)
def update_salida(
    salida_id: str,
    payload: SalidaCanalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Guarda la edición del socio (bloques editados, asunto, destinatarios, estado)."""
    _require_admin(current_user)
    s = db.query(SalidaCanal).filter(SalidaCanal.id == salida_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Salida no encontrada")
    if payload.contenido_editado is not None:
        s.contenido_editado = json.dumps(payload.contenido_editado, ensure_ascii=False)
    if payload.meta is not None:
        s.meta = json.dumps(payload.meta, ensure_ascii=False)
    if payload.estado is not None:
        s.estado = payload.estado
    s.updated_at = get_utc_now()
    db.commit()
    db.refresh(s)
    return _salida_response(s)


def _contenido_y_meta(s: SalidaCanal):
    contenido = {}
    if s.contenido_editado:
        contenido = json.loads(s.contenido_editado)
    elif s.contenido_generado:
        contenido = json.loads(s.contenido_generado)
    meta = {}
    if s.meta:
        try:
            meta = json.loads(s.meta)
        except Exception:
            meta = {}
    return contenido, meta


@router.get("/{publicacion_id}/correo/html", response_class=HTMLResponse)
def correo_html(
    publicacion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Devuelve el HTML email-safe maquetado (para preview y copiar)."""
    _require_admin(current_user)
    s = (
        db.query(SalidaCanal)
        .filter(SalidaCanal.publicacion_id == publicacion_id, SalidaCanal.canal == "correo")
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="Aún no se ha adaptado el correo")
    contenido, meta = _contenido_y_meta(s)
    firma = meta.get("firma") or (current_user.email_signature or "El equipo de ASIC XXI")
    from app.utils.comunicaciones_ai import build_email_html
    from app.config import get_settings
    cfg = get_settings()
    logo_url = (cfg.public_base_url.rstrip("/") + "/static/img/asicxxi_logo.png") if cfg.public_base_url else ""
    html = build_email_html(
        contenido, firma=firma, saludo=meta.get("saludo", "Hola"),
        logo_url=logo_url,
        cta_web=cfg.comunicaciones_cta_web,
        cta_email=cfg.comunicaciones_cta_email,
        cta_tel=cfg.comunicaciones_cta_tel,
    )
    return HTMLResponse(content=html)


@router.get("/{publicacion_id}/correo/eml")
def correo_eml(
    publicacion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Descarga un .eml con To/CC/BCC + HTML listo para abrir en Outlook."""
    _require_admin(current_user)
    s = (
        db.query(SalidaCanal)
        .filter(SalidaCanal.publicacion_id == publicacion_id, SalidaCanal.canal == "correo")
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="Aún no se ha adaptado el correo")
    contenido, meta = _contenido_y_meta(s)
    firma = meta.get("firma") or (current_user.email_signature or "El equipo de ASIC XXI")

    from app.utils.comunicaciones_ai import build_email_html
    from app.config import get_settings
    from email.message import EmailMessage
    cfg = get_settings()
    logo_url = (cfg.public_base_url.rstrip("/") + "/static/img/asicxxi_logo.png") if cfg.public_base_url else ""
    html = build_email_html(
        contenido, firma=firma, saludo=meta.get("saludo", "Hola"),
        logo_url=logo_url,
        cta_web=cfg.comunicaciones_cta_web,
        cta_email=cfg.comunicaciones_cta_email,
        cta_tel=cfg.comunicaciones_cta_tel,
    )

    def _join(lst):
        return ", ".join([x for x in (lst or []) if x])

    msg = EmailMessage()
    # X-Unsent:1 hace que Outlook abra el .eml como mensaje NUEVO editable/enviable
    # (en vez de en modo lectura como un correo ya recibido).
    msg["X-Unsent"] = "1"
    msg["Subject"] = meta.get("asunto", "Novedades BOMP")
    to = _join(meta.get("destinatarios_to"))
    cc = _join(meta.get("destinatarios_cc"))
    bcc = _join(meta.get("destinatarios_bcc") or meta.get("destinatarios_extra"))
    if to:
        msg["To"] = to
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc
    msg.set_content("Tu cliente de correo no soporta HTML. Abre el mensaje en un cliente compatible.")
    # base64 evita los artefactos '=' de quoted-printable (asicx=i.es) al partir lineas largas
    msg.add_alternative(html, subtype="html", cte="base64")

    eml_bytes = msg.as_bytes()
    return Response(
        content=eml_bytes,
        media_type="message/rfc822",
        headers={"Content-Disposition": 'attachment; filename="novedades_bomp.eml"'},
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


# ===========================================================================
# Prompts del adaptador (versiones + hero level + calibración/feedback)
# Router aparte con prefijo más específico, registrado ANTES del router
# principal para que /comunicaciones/prompts no colisione con /{publicacion_id}.
# ===========================================================================

prompts_router = APIRouter(prefix="/comunicaciones/prompts", tags=["Comunicaciones Prompts"])


def _prompt_response(p: ComunicacionPrompt) -> PromptResponse:
    return PromptResponse(
        id=p.id, nombre=p.nombre, canal=p.canal, prompt_text=p.prompt_text,
        hero_level=p.hero_level, calibracion=p.calibracion, activa=bool(p.activa),
    )


@prompts_router.get("", response_model=PromptListResponse)
def list_prompts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    _require_admin(current_user)
    from app.utils.comunicaciones_ai import SYSTEM_PROMPT_CORREO
    items = db.query(ComunicacionPrompt).filter(ComunicacionPrompt.canal == "correo").order_by(ComunicacionPrompt.created_at.asc()).all()
    return PromptListResponse(
        prompts=[_prompt_response(p) for p in items],
        default_prompt=SYSTEM_PROMPT_CORREO,
    )


@prompts_router.post("", response_model=PromptResponse, status_code=201)
def create_prompt(
    payload: PromptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    _require_admin(current_user)
    now = get_utc_now()
    p = ComunicacionPrompt(
        id=generate_id(), nombre=payload.nombre.strip(), canal="correo",
        prompt_text=(payload.prompt_text or "").strip() or None,
        hero_level=payload.hero_level, calibracion=(payload.calibracion or "").strip() or None,
        activa=0, created_at=now, updated_at=now,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _prompt_response(p)


@prompts_router.patch("/{prompt_id}", response_model=PromptResponse)
def update_prompt(
    prompt_id: str,
    payload: PromptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    _require_admin(current_user)
    p = db.query(ComunicacionPrompt).filter(ComunicacionPrompt.id == prompt_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Prompt no encontrado")
    if payload.nombre is not None: p.nombre = payload.nombre.strip()
    if payload.prompt_text is not None: p.prompt_text = payload.prompt_text.strip() or None
    if payload.hero_level is not None: p.hero_level = payload.hero_level
    if payload.calibracion is not None: p.calibracion = payload.calibracion.strip() or None
    p.updated_at = get_utc_now()
    db.commit()
    db.refresh(p)
    return _prompt_response(p)


@prompts_router.post("/{prompt_id}/activar", response_model=PromptResponse)
def activar_prompt(
    prompt_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    _require_admin(current_user)
    p = db.query(ComunicacionPrompt).filter(ComunicacionPrompt.id == prompt_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Prompt no encontrado")
    db.query(ComunicacionPrompt).filter(ComunicacionPrompt.canal == "correo").update({"activa": 0})
    p.activa = 1
    p.updated_at = get_utc_now()
    db.commit()
    db.refresh(p)
    return _prompt_response(p)


@prompts_router.delete("/{prompt_id}", status_code=204)
def delete_prompt(
    prompt_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    _require_admin(current_user)
    p = db.query(ComunicacionPrompt).filter(ComunicacionPrompt.id == prompt_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="No encontrado")
    db.delete(p)
    db.commit()
    return None


@prompts_router.post("/feedback", status_code=200)
def feedback_calibracion(
    payload: FeedbackItem,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """
    Añade un ejemplo de calibración (bien/meh/mal) al prompt ACTIVO desde la
    pantalla de curación. Si no hay prompt activo, crea uno por defecto editable.
    """
    _require_admin(current_user)
    activa = (
        db.query(ComunicacionPrompt)
        .filter(ComunicacionPrompt.canal == "correo", ComunicacionPrompt.activa == 1)
        .first()
    )
    if not activa:
        now = get_utc_now()
        activa = ComunicacionPrompt(
            id=generate_id(), nombre="Prompt activo (auto)", canal="correo",
            prompt_text=None, hero_level=2, calibracion=None, activa=1,
            created_at=now, updated_at=now,
        )
        db.add(activa)
        db.flush()

    marca = {"bien": "BIEN ✅", "meh": "MEH 😐", "mal": "MAL ❌"}.get(payload.veredicto, payload.veredicto)
    linea = f'- {marca} titulo: "{(payload.titulo or "").strip()}". cuerpo: "{(payload.cuerpo or "").strip()}".'
    if payload.nota:
        linea += f' Nota del revisor: {payload.nota.strip()}'
    activa.calibracion = ((activa.calibracion or "") + "\n" + linea).strip()
    activa.updated_at = get_utc_now()
    db.commit()
    return {"ok": True, "prompt_id": activa.id}
