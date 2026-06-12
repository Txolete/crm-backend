"""
Endpoints for email templates + sent registry.

MVP: Admin gestiona plantillas. Comerciales eligen plantilla, rellenan variables,
renderizan y registran envio (vinculado a cuenta/contacto/oportunidad).
El envio fisico se delega al cliente de correo del usuario (mailto:) o copia al portapapeles.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List
from datetime import datetime, timezone
import re
import logging

from app.database import get_db
from app.models.user import User
from app.models.email_template import EmailTemplate, EmailSent
from app.schemas.email_template import (
    EmailTemplateCreate, EmailTemplateUpdate, EmailTemplateResponse, EmailTemplateListResponse,
    RenderRequest, RenderResponse,
    EmailSentCreate, EmailSentResponse, EmailSentListResponse, MarkResponseRequest,
)
from app.utils.auth import get_current_user_from_cookie
from app.utils.audit import generate_id, get_utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email-templates", tags=["Email Templates"])
sent_router = APIRouter(prefix="/emails-sent", tags=["Emails Sent"])
templates = Jinja2Templates(directory="app/templates")


# ---------------------------------------------------------------------------
# Render helper
# ---------------------------------------------------------------------------

_VAR_RE = re.compile(r"\{\{\s*([a-z_][a-z0-9_]*)\s*\}\}", re.IGNORECASE)


def _normalize_var(name: str) -> str:
    """Acepta variantes con/sin tildes (señal_detectada -> senal_detectada)."""
    n = name.strip().lower()
    n = n.replace("ñ", "n").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    return n


def _render(text: str, variables: dict) -> str:
    norm_vars = {_normalize_var(k): v for k, v in variables.items()}

    def repl(m):
        key = _normalize_var(m.group(1))
        return str(norm_vars.get(key, m.group(0)))

    return _VAR_RE.sub(repl, text or "")


def _extract_vars(text: str) -> List[str]:
    seen = []
    for m in _VAR_RE.finditer(text or ""):
        v = _normalize_var(m.group(1))
        if v not in seen:
            seen.append(v)
    return seen


def _to_template_response(db: Session, t: EmailTemplate) -> EmailTemplateResponse:
    sent_count = db.query(func.count(EmailSent.id)).filter(EmailSent.template_id == t.id).scalar() or 0
    resp_count = db.query(func.count(EmailSent.id)).filter(
        EmailSent.template_id == t.id, EmailSent.response_received == 1
    ).scalar() or 0
    return EmailTemplateResponse(
        id=t.id, name=t.name, category=t.category, subject=t.subject, body=t.body,
        required_variables=t.required_variables, notes=t.notes,
        is_active=bool(t.is_active),
        created_at=t.created_at, updated_at=t.updated_at,
        sent_count=sent_count, response_count=resp_count,
    )


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

@router.get("/page", response_class=HTMLResponse)
async def templates_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
):
    return templates.TemplateResponse("email_templates.html", {"request": request})


# ---------------------------------------------------------------------------
# Seed inicial idempotente (por si la migracion no sembro las dos plantillas base)
# ---------------------------------------------------------------------------

_SEED_TEMPLATES = [
    {
        "name": "Email frío estándar (PYME / mid-market)",
        "category": "cold-standard",
        "subject": "Vuestra operativa como comercializadora",
        "body": (
            "Hola {{nombre}},\n\n"
            "He visto que {{senal_detectada}}. Enhorabuena — y prepárate, porque OMIE, REE, las distribuidoras "
            "y la CNMC no esperan, y cada cambio regulatorio rompe algo.\n\n"
            "A eso nos dedicamos: llevamos el back office de más de 60 comercializadoras desde 2017, con BOMP, "
            "nuestro ERP nacido para este mercado. Hay quien nos usa como equipo externo, quien solo usa el "
            "software y quien combina ambos.\n\n"
            "¿Te encajan 15 minutos esta semana para ver qué encaja en vuestro caso?\n\n"
            "{{firma_comercial}}\nASIC XXI"
        ),
        "required_variables": "nombre,senal_detectada,firma_comercial",
        "notes": (
            "Comercializadoras pequeñas/medianas. <100 palabras, sin adjuntos, un único CTA: reunión de 15 minutos. "
            "Personalizar SIEMPRE la señal detectada (sin señal, no se envía)."
        ),
    },
    {
        "name": "Email frío corporate / TIER 1 (Shell, UNIPER, etc.)",
        "category": "cold-corporate",
        "subject": "Mercado energético español / apoyo operativo local",
        "body": (
            "Hola {{nombre}},\n\n"
            "He visto que {{empresa}} opera a una escala muy corporativa en trading, gas, electricidad y "
            "soluciones energéticas, así que no tendría sentido plantearos una herramienta genérica ni intentar "
            "sustituir sistemas globales.\n\n"
            "Donde ASICXXI sí puede aportar valor es en proyectos concretos en Iberia cuando hace falta aterrizar "
            "actividad en el mercado español: CNMC, OMIE, REE, MITECO, ENAGAS, CORES, MIBGAS, switching, "
            "facturación, reporting, previsión de demanda, gestión de desvíos, garantías y modelo operativo "
            "de comercialización, consumidores directos, etc.\n\n"
            "Imagino que para consultoría estratégica o regulatoria global ya trabajáis con firmas grandes. "
            "Nuestro enfoque es distinto: asesoría senior, muy especializada en operación real de agentes, "
            "sin capas de juniors ni estructura pesada de consultora generalista. Menos presentación corporativa "
            "y más ejecución práctica: trámites, procesos, sistemas, automatización y puesta en marcha.\n\n"
            "Podemos actuar como apoyo especialista local, tanto si se trata de una unidad propia, un partner "
            "o un proyecto en España/Iberia que necesite conocimiento operativo del mercado.\n\n"
            "{{senal_detectada}}\n\n"
            "¿Tiene sentido que lo validemos brevemente, o ahora mismo no tenéis ningún frente activo en esta línea?\n\n"
            "Un saludo,\n{{firma_comercial}}"
        ),
        "required_variables": "nombre,empresa,senal_detectada,firma_comercial",
        "notes": (
            "Para corporaciones grandes que NO van a comprar back office completo pero pueden necesitar apoyo "
            "en proyectos puntuales en Iberia. Tono más senior, menos comercial, ofreciendo ejecución práctica "
            "vs consultora generalista."
        ),
    },
]


@router.post("/seed-initial")
def seed_initial_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """
    Siembra las 2 plantillas base si no existen ya (por categoria). Idempotente.
    Util cuando la migracion no llego a sembrar (deploy en cliente con BD ya existente).
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    now = get_utc_now()
    created = []
    skipped = []
    for seed in _SEED_TEMPLATES:
        exists = (
            db.query(EmailTemplate)
            .filter(EmailTemplate.category == seed["category"])
            .first()
        )
        if exists:
            skipped.append({"category": seed["category"], "id": exists.id, "name": exists.name})
            continue
        t = EmailTemplate(
            id=generate_id(),
            name=seed["name"],
            category=seed["category"],
            subject=seed["subject"],
            body=seed["body"],
            required_variables=seed["required_variables"],
            notes=seed["notes"],
            is_active=1,
            created_at=now,
            updated_at=now,
            created_by_user_id=current_user.id,
        )
        db.add(t)
        db.flush()
        created.append({"category": seed["category"], "id": t.id, "name": t.name})
    db.commit()
    logger.info(f"[email-templates] seed created={len(created)} skipped={len(skipped)}")
    return {"created": created, "skipped": skipped}


# ---------------------------------------------------------------------------
# Template CRUD
# ---------------------------------------------------------------------------

@router.get("", response_model=EmailTemplateListResponse)
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
    include_inactive: bool = False,
):
    q = db.query(EmailTemplate)
    if not include_inactive:
        q = q.filter(EmailTemplate.is_active == 1)
    items = q.order_by(EmailTemplate.category.asc(), EmailTemplate.name.asc()).all()
    return EmailTemplateListResponse(
        templates=[_to_template_response(db, t) for t in items],
        total=len(items),
    )


@router.post("", response_model=EmailTemplateResponse, status_code=201)
def create_template(
    payload: EmailTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin puede crear plantillas")
    now = get_utc_now()
    t = EmailTemplate(
        id=generate_id(),
        name=payload.name.strip(),
        category=(payload.category or "").strip() or None,
        subject=payload.subject.strip(),
        body=payload.body,
        required_variables=payload.required_variables.strip(),
        notes=payload.notes,
        is_active=1 if payload.is_active else 0,
        created_at=now,
        updated_at=now,
        created_by_user_id=current_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return _to_template_response(db, t)


@router.get("/{template_id}", response_model=EmailTemplateResponse)
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return _to_template_response(db, t)


@router.patch("/{template_id}", response_model=EmailTemplateResponse)
def update_template(
    template_id: str,
    payload: EmailTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="No encontrada")
    if payload.name is not None: t.name = payload.name.strip()
    if payload.category is not None: t.category = payload.category.strip() or None
    if payload.subject is not None: t.subject = payload.subject.strip()
    if payload.body is not None: t.body = payload.body
    if payload.required_variables is not None: t.required_variables = payload.required_variables.strip()
    if payload.notes is not None: t.notes = payload.notes
    if payload.is_active is not None: t.is_active = 1 if payload.is_active else 0
    t.updated_at = get_utc_now()
    db.commit()
    db.refresh(t)
    return _to_template_response(db, t)


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="No encontrada")
    # Si tiene envios asociados, mejor desactivar que borrar
    has_sent = db.query(EmailSent.id).filter(EmailSent.template_id == template_id).first()
    if has_sent:
        t.is_active = 0
        t.updated_at = get_utc_now()
        db.commit()
        return None
    db.delete(t)
    db.commit()
    return None


@router.post("/{template_id}/render", response_model=RenderResponse)
def render_template(
    template_id: str,
    payload: RenderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """
    Renderiza la plantilla con las variables provistas.
    Si faltan obligatorias, devuelve missing_required (no bloquea — bloquea el endpoint POST /emails-sent).
    """
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="No encontrada")
    required = [_normalize_var(v) for v in (t.required_variables or "").split(",") if v.strip()]
    norm_vars = {_normalize_var(k): (v or "").strip() for k, v in (payload.variables or {}).items()}
    missing = [r for r in required if not norm_vars.get(r)]
    return RenderResponse(
        subject=_render(t.subject, payload.variables),
        body=_render(t.body, payload.variables),
        missing_required=missing,
    )


# ---------------------------------------------------------------------------
# Emails Sent
# ---------------------------------------------------------------------------

@sent_router.post("", response_model=EmailSentResponse, status_code=201)
def record_sent(
    payload: EmailSentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """
    Registra que se ha enviado un email (via cliente de correo del usuario).
    Si viene de una plantilla y esa plantilla tiene senal_detectada como obligatoria, se valida.
    """
    template_name = None
    if payload.template_id:
        t = db.query(EmailTemplate).filter(EmailTemplate.id == payload.template_id).first()
        if not t:
            raise HTTPException(status_code=404, detail="Plantilla no encontrada")
        template_name = t.name
        required = [_normalize_var(v) for v in (t.required_variables or "").split(",") if v.strip()]
        if "senal_detectada" in required and not (payload.senal_detectada or "").strip():
            raise HTTPException(
                status_code=400,
                detail="Falta 'senal_detectada' — esta plantilla la marca obligatoria (regla de la guia: sin senal, no se envia)",
            )

    if not (payload.to_email or "").strip():
        raise HTTPException(status_code=400, detail="to_email es obligatorio")

    e = EmailSent(
        id=generate_id(),
        template_id=payload.template_id,
        template_name_snapshot=template_name,
        account_id=payload.account_id,
        contact_id=payload.contact_id,
        opportunity_id=payload.opportunity_id,
        to_email=payload.to_email.strip(),
        to_name=(payload.to_name or "").strip() or None,
        subject=payload.subject,
        body=payload.body,
        senal_detectada=(payload.senal_detectada or "").strip() or None,
        sent_at=get_utc_now(),
        sent_by_user_id=current_user.id,
        response_received=0,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    logger.info(f"[email] registrado envio template={payload.template_id} account={payload.account_id} contact={payload.contact_id}")
    return _to_sent_response(db, e, current_user.name)


@sent_router.get("", response_model=EmailSentListResponse)
def list_sent(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
    account_id: Optional[str] = None,
    contact_id: Optional[str] = None,
    opportunity_id: Optional[str] = None,
    template_id: Optional[str] = None,
    limit: int = Query(200, le=500),
):
    q = db.query(EmailSent)
    if account_id: q = q.filter(EmailSent.account_id == account_id)
    if contact_id: q = q.filter(EmailSent.contact_id == contact_id)
    if opportunity_id: q = q.filter(EmailSent.opportunity_id == opportunity_id)
    if template_id: q = q.filter(EmailSent.template_id == template_id)
    if current_user.role == "commercial":
        q = q.filter(EmailSent.sent_by_user_id == current_user.id)
    items = q.order_by(desc(EmailSent.sent_at)).limit(limit).all()
    user_ids = {i.sent_by_user_id for i in items if i.sent_by_user_id}
    users = {u.id: u.name for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    return EmailSentListResponse(
        emails=[_to_sent_response(db, i, users.get(i.sent_by_user_id)) for i in items],
        total=len(items),
    )


@sent_router.patch("/{email_id}/response", response_model=EmailSentResponse)
def mark_response(
    email_id: str,
    payload: MarkResponseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    e = db.query(EmailSent).filter(EmailSent.id == email_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="No encontrado")
    e.response_received = 1 if payload.response_received else 0
    e.response_at = get_utc_now() if payload.response_received else None
    if payload.response_note is not None:
        e.response_note = payload.response_note
    db.commit()
    db.refresh(e)
    sender = db.query(User.name).filter(User.id == e.sent_by_user_id).scalar() if e.sent_by_user_id else None
    return _to_sent_response(db, e, sender)


def _to_sent_response(db: Session, e: EmailSent, sent_by_name: Optional[str] = None) -> EmailSentResponse:
    return EmailSentResponse(
        id=e.id, template_id=e.template_id, template_name_snapshot=e.template_name_snapshot,
        account_id=e.account_id, contact_id=e.contact_id, opportunity_id=e.opportunity_id,
        to_email=e.to_email, to_name=e.to_name, subject=e.subject, body=e.body,
        senal_detectada=e.senal_detectada,
        sent_at=e.sent_at, sent_by_user_id=e.sent_by_user_id, sent_by_name=sent_by_name,
        response_received=bool(e.response_received),
        response_at=e.response_at, response_note=e.response_note,
    )
