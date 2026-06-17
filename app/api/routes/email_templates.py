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
sequence_router = APIRouter(prefix="/opportunities", tags=["Email Sequence"])
templates = Jinja2Templates(directory="app/templates")


# ---------------------------------------------------------------------------
# Mapeo de toques -> categorias de plantilla
# Aprovechamos los EmailSent ya guardados para reconstruir la secuencia,
# sin meter campos nuevos en Opportunity.
# ---------------------------------------------------------------------------

TOUCH_DEFINITIONS = [
    {"step": 0, "label": "Toque 0 — Email frío",            "categories": ["cold-standard", "cold-corporate"]},
    {"step": 1, "label": "Toque 1 — Valor regulatorio (+3 días)", "categories": ["follow-up-1"]},
    {"step": 2, "label": "Toque 2 — Prueba social + deck (+5 días)", "categories": ["follow-up-2"]},
    {"step": 3, "label": "Toque 3 — Cierre limpio (+7 días)",     "categories": ["follow-up-3"]},
]

ALL_SEQUENCE_CATEGORIES = {c for d in TOUCH_DEFINITIONS for c in d["categories"]}


def get_sequence_state(db: Session, opportunity_id: str) -> dict:
    """
    Devuelve el estado de la secuencia de seguimiento de una oportunidad.
    Reconstruye los toques desde EmailSent agrupados por category de la plantilla.
    """
    sent = (
        db.query(EmailSent)
        .filter(EmailSent.opportunity_id == opportunity_id)
        .order_by(EmailSent.sent_at.asc())
        .all()
    )

    # Cargar plantillas implicadas para conocer su categoria
    tpl_ids = list({e.template_id for e in sent if e.template_id})
    tpls = {}
    if tpl_ids:
        for t in db.query(EmailTemplate).filter(EmailTemplate.id.in_(tpl_ids)).all():
            tpls[t.id] = t

    # Index: categoria -> primer EmailSent que la usa
    sent_by_category = {}
    for e in sent:
        cat = tpls.get(e.template_id).category if (e.template_id and tpls.get(e.template_id)) else None
        if cat and cat not in sent_by_category:
            sent_by_category[cat] = e

    # any_response: cualquier EmailSent de esta oportunidad con response_received
    any_response = any(e.response_received == 1 for e in sent)

    # Plantillas activas disponibles agrupadas por categoria
    available = {}
    for t in db.query(EmailTemplate).filter(
        EmailTemplate.is_active == 1,
        EmailTemplate.category.in_(list(ALL_SEQUENCE_CATEGORIES))
    ).all():
        available.setdefault(t.category, []).append({"id": t.id, "name": t.name})

    touches = []
    count_sent = 0
    for d in TOUCH_DEFINITIONS:
        match = None
        for cat in d["categories"]:
            if cat in sent_by_category:
                match = sent_by_category[cat]
                break
        sent_at = None
        responded = False
        email_sent_id = None
        subject = None
        if match:
            count_sent += 1
            sent_at = match.sent_at.isoformat() if match.sent_at else None
            responded = bool(match.response_received)
            email_sent_id = match.id
            subject = match.subject

        avail = []
        for cat in d["categories"]:
            for t in available.get(cat, []):
                avail.append({**t, "category": cat})

        touches.append({
            "step": d["step"],
            "label": d["label"],
            "categories": d["categories"],
            "sent": match is not None,
            "sent_at": sent_at,
            "email_sent_id": email_sent_id,
            "subject": subject,
            "responded": responded,
            "available_templates": avail,
        })

    return {
        "opportunity_id": opportunity_id,
        "touches": touches,
        "any_response": any_response,
        "count_sent": count_sent,
        "total": len(TOUCH_DEFINITIONS),
    }


def get_sequence_progress_batch(db: Session, opportunity_ids: list) -> dict:
    """
    Variante optimizada para Kanban: devuelve solo (count_sent, any_response) por opp_id.
    """
    if not opportunity_ids:
        return {}
    tpls = {
        t.id: t.category for t in db.query(EmailTemplate).filter(
            EmailTemplate.category.in_(list(ALL_SEQUENCE_CATEGORIES))
        ).all()
    }
    sent = db.query(EmailSent).filter(
        EmailSent.opportunity_id.in_(opportunity_ids)
    ).all()

    result = {oid: {"count_sent": 0, "any_response": False, "categories_sent": set()} for oid in opportunity_ids}
    for e in sent:
        if not e.opportunity_id:
            continue
        r = result.get(e.opportunity_id)
        if not r:
            continue
        if e.response_received == 1:
            r["any_response"] = True
        cat = tpls.get(e.template_id) if e.template_id else None
        if cat:
            r["categories_sent"].add(cat)

    # count_sent = numero de toques (no de emails) — agrupar por toque definicion
    for oid, r in result.items():
        touches_sent = 0
        for d in TOUCH_DEFINITIONS:
            if any(c in r["categories_sent"] for c in d["categories"]):
                touches_sent += 1
        r["count_sent"] = touches_sent
        del r["categories_sent"]  # no la exponemos
    return result


@sequence_router.get("/{opportunity_id}/email-sequence")
def get_opportunity_sequence(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """Estado de la secuencia de 4 toques (0-3) para una oportunidad."""
    return get_sequence_state(db, opportunity_id)


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
        "name": "Seguimiento — Toque 1: valor regulatorio (+3 días)",
        "category": "follow-up-1",
        "subject": "{{novedad_regulatoria}} — ojo al plazo",
        "body": (
            "{{nombre}},\n\n"
            "{{novedad_regulatoria}}. Os toca.\n\n"
            "Lo veo de cerca porque a nosotros nos toca adaptarlo para las comercializadoras que llevamos. "
            "Por si os pilla liados.\n\n"
            "{{firma_comercial}}"
        ),
        "required_variables": "nombre,novedad_regulatoria,firma_comercial",
        "notes": (
            "Toque 1 de la secuencia de 3. Ángulo: aportar valor sin pedir nada. NO hay CTA — el valor ES el mensaje. "
            "novedad_regulatoria = una frase real y vigente esta semana (BOE / CNMC / OMIE / REE) con la obligación + plazo. "
            "Si esa semana no hay novedad regulatoria real, NO se manda este toque (la guía dice: inventarse uno hace el efecto contrario)."
        ),
    },
    {
        "name": "Seguimiento — Toque 2: prueba social + deck (+5 días)",
        "category": "follow-up-2",
        "subject": "Otras como {{referencia}} ya lo delegan",
        "body": (
            "{{nombre}},\n\n"
            "Te escribí hace unos días. Igual no era el momento.\n\n"
            "Al grano: más de 60 comercializadoras nos pasan la operativa que quema horas y no da ingresos — "
            "facturación, ATR, desvíos, garantías, reporting. Varias arrancaron donde estáis vosotros ahora.\n\n"
            "Te dejo 6 diapositivas, 2 minutos de lectura. Si ves algo que encaja, ¿{{propuesta_hueco}}?\n\n"
            "{{firma_comercial}}"
        ),
        "required_variables": "nombre,referencia,propuesta_hueco,firma_comercial",
        "notes": (
            "Toque 2 de la secuencia. Es el ÚNICO que adjunta el deck outbound (6 slides), descargable desde Material. "
            "referencia = una comercializadora cliente del tamaño/perfil del lead (Paratí, Enersa…). Si no quieres exponer un nombre, "
            'usa asunto alternativo "Cómo lo llevan otras de vuestro tamaño". '
            'propuesta_hueco = franja concreta, no "cuándo te viene bien" (ej: "el jueves a las 10").'
        ),
    },
    {
        "name": "Seguimiento — Toque 3: cierre limpio (+7 días)",
        "category": "follow-up-3",
        "subject": "Lo dejo aquí",
        "body": (
            "{{nombre}},\n\n"
            "Última por ahora, que tampoco quiero ocupar bandeja para nada.\n\n"
            "Si la operativa hoy no aprieta, perfecto. Suele apretar cuando crece la cartera o llega un cambio "
            "normativo cruzado. Ese día estamos.\n\n"
            "Si quieres, te dejo en la lista de avisos regulatorios y nada más. ¿Te apunto?\n\n"
            "{{firma_comercial}}"
        ),
        "required_variables": "nombre,firma_comercial",
        "notes": (
            "Toque 3 / break-up. Cierra y deja la puerta entornada. Va seco a propósito (la insistencia personalizada cansa). "
            "La última pregunta reconvierte el 'no' en alta voluntaria a la newsletter: quien contesta 'sí, apúntame' pasa "
            "a base templada en vez de perderse. Tras este toque sin respuesta, la oportunidad se aparca (no se marca como perdida)."
        ),
    },
    {
        "name": "Email frío estándar (PYME / mid-market)",
        "category": "cold-standard",
        "subject": "Vuestra operativa como comercializadora",
        "body": (
            "Hola {{nombre}},\n\n"
            "He visto {{senal_detectada}}. Enhorabuena — y prepárate, porque OMIE, REE, las distribuidoras "
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
            "¿Tiene sentido que lo validemos brevemente, o ahora mismo no tenéis ningún frente activo en esta línea?\n\n"
            "Un saludo,\n{{firma_comercial}}"
        ),
        "required_variables": "nombre,empresa,firma_comercial",
        "notes": (
            "Para corporaciones grandes que NO van a comprar back office completo pero pueden necesitar apoyo "
            "en proyectos puntuales en Iberia. Tono más senior, menos comercial, ofreciendo ejecución práctica "
            "vs consultora generalista."
        ),
    },
]


@router.post("/seed-initial")
def seed_initial_templates(
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    """
    Siembra las plantillas base por categoria.
    - Sin force: idempotente, solo crea las que no existen.
    - Con force=True: pisa asunto/cuerpo/required/notes de las que ya existen (mantiene el id).
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo admin")
    now = get_utc_now()
    created = []
    updated = []
    skipped = []
    for seed in _SEED_TEMPLATES:
        exists = (
            db.query(EmailTemplate)
            .filter(EmailTemplate.category == seed["category"])
            .first()
        )
        if exists:
            if force:
                exists.name = seed["name"]
                exists.subject = seed["subject"]
                exists.body = seed["body"]
                exists.required_variables = seed["required_variables"]
                exists.notes = seed["notes"]
                exists.is_active = 1
                exists.updated_at = now
                updated.append({"category": seed["category"], "id": exists.id, "name": exists.name})
            else:
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
    logger.info(f"[email-templates] seed force={force} created={len(created)} updated={len(updated)} skipped={len(skipped)}")
    return {"created": created, "updated": updated, "skipped": skipped}


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
        cc_emails=(payload.cc_emails or "").strip() or None,
        bcc_emails=(payload.bcc_emails or "").strip() or None,
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
        to_email=e.to_email, to_name=e.to_name,
        cc_emails=e.cc_emails, bcc_emails=e.bcc_emails,
        subject=e.subject, body=e.body,
        senal_detectada=e.senal_detectada,
        sent_at=e.sent_at, sent_by_user_id=e.sent_by_user_id, sent_by_name=sent_by_name,
        response_received=bool(e.response_received),
        response_at=e.response_at, response_note=e.response_note,
    )
