"""
AI Integration endpoints — Sprint 4E

POST /opportunities/{id}/ai/analyze  — genera/actualiza síntesis ejecutiva
POST /opportunities/{id}/ai/chat     — mensaje libre al thread de la oportunidad
GET  /opportunities/{id}/ai/history  — historial del thread
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.opportunity import Opportunity, Task, Activity
from app.models.account import Account, Contact, ContactChannel
from app.models.user import User
from app.utils.auth import get_current_user_from_cookie, require_role
from app.utils.audit import get_utc_now
from app.utils.ai_service import get_ai_provider, build_opportunity_context

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI"])


# ============================================================================
# SCHEMAS
# ============================================================================

class AIAnalyzeResponse(BaseModel):
    executive_summary: str
    thread_id: str
    message: str = "Análisis completado"


class AIChatRequest(BaseModel):
    message: str


class AIChatResponse(BaseModel):
    response: str
    thread_id: str


class AIHistoryMessage(BaseModel):
    role: str
    content: str
    created_at: Optional[int] = None


class AIHistoryResponse(BaseModel):
    thread_id: str
    messages: list[AIHistoryMessage]


# ============================================================================
# HELPERS
# ============================================================================

def _get_opportunity_or_404(opportunity_id: str, db: Session) -> Opportunity:
    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    return opp


def _build_context_for_opportunity(opportunity_id: str, db: Session) -> tuple:
    """Carga todos los datos necesarios para el contexto AI."""
    from app.models.config import (
        CfgStage, CfgStageProbability, CfgOpportunityType,
        CfgClientMentalState, CfgLostReason, CfgRegion, CfgCustomerType
    )
    from app.models.user import User as UserModel

    opp = _get_opportunity_or_404(opportunity_id, db)

    # Enriquecer oportunidad con nombres de relaciones
    account = db.query(Account).filter(Account.id == opp.account_id).first()
    stage = db.query(CfgStage).filter(CfgStage.id == opp.stage_id).first()
    stage_prob = db.query(CfgStageProbability).filter(CfgStageProbability.stage_id == opp.stage_id).first()
    owner = db.query(UserModel).filter(UserModel.id == opp.owner_user_id).first() if opp.owner_user_id else None

    opp.account_name = account.name if account else ""
    opp.stage_name = stage.name if stage else ""
    opp.stage_probability = stage_prob.probability if stage_prob else None
    opp.owner_user_name = owner.name if owner else ""

    if opp.opportunity_type_id:
        ot = db.query(CfgOpportunityType).filter(CfgOpportunityType.id == opp.opportunity_type_id).first()
        opp.opportunity_type_name = ot.name if ot else None

    if opp.client_mental_state_id:
        ms = db.query(CfgClientMentalState).filter(CfgClientMentalState.id == opp.client_mental_state_id).first()
        opp.client_mental_state_name = ms.name if ms else None

    # Enriquecer cuenta con relaciones (región, tipo de cliente)
    if account:
        if account.region_id:
            region = db.query(CfgRegion).filter(CfgRegion.id == account.region_id).first()
            account.region_name = region.name if region else account.region_other_text or ""
        else:
            account.region_name = account.region_other_text or ""

        if account.customer_type_id:
            ctype = db.query(CfgCustomerType).filter(CfgCustomerType.id == account.customer_type_id).first()
            account.customer_type_name = ctype.name if ctype else account.customer_type_other_text or ""
        else:
            account.customer_type_name = account.customer_type_other_text or ""

    # Contactos de la cuenta con sus canales
    contacts = db.query(Contact).filter(Contact.account_id == opp.account_id).all()
    for c in contacts:
        c.channels = db.query(ContactChannel).filter(ContactChannel.contact_id == c.id).all()

    # Todas las actividades de la oportunidad (sin límite, ordenadas cronológicamente)
    activities = db.query(Activity).filter(
        Activity.opportunity_id == opportunity_id
    ).order_by(Activity.occurred_at.asc()).all()

    # Tareas
    tasks = db.query(Task).filter(
        Task.opportunity_id == opportunity_id
    ).order_by(Task.due_date).all()

    return opp, account, contacts, activities, tasks


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/opportunities/{opportunity_id}/ai/analyze", response_model=AIAnalyzeResponse)
async def analyze_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Genera o actualiza la síntesis ejecutiva de una oportunidad usando IA.

    - Construye el contexto completo (datos, contactos, actividades, tareas)
    - Lo envía al provider de IA configurado (OpenAI por defecto)
    - Si ya existe un thread para esta oportunidad, continúa la conversación
    - Guarda la síntesis en executive_summary y el thread_id en BD
    """
    try:
        ai = get_ai_provider()
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    try:
        opp, account, contacts, activities, tasks = _build_context_for_opportunity(opportunity_id, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AI] Error building context for {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar contexto de la oportunidad: {str(e)}"
        )

    try:
        context = build_opportunity_context(opp, account, contacts, activities, tasks)
    except Exception as e:
        logger.error(f"[AI] Error building prompt for {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al construir el prompt: {str(e)}"
        )

    logger.info(f"[AI] Analyzing opportunity {opportunity_id} (thread: {opp.chatgpt_thread_id})")

    try:
        synthesis, thread_id = ai.analyze_opportunity(context, thread_id=opp.chatgpt_thread_id)
    except Exception as e:
        logger.error(f"[AI] Provider error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI provider error: {str(e)}"
        )

    # Guardar síntesis y thread_id en BD
    opp.executive_summary = synthesis
    opp.chatgpt_thread_id = thread_id
    opp.updated_at = get_utc_now()
    db.commit()

    logger.info(f"[AI] Opportunity {opportunity_id} analyzed. Thread: {thread_id}")

    return AIAnalyzeResponse(
        executive_summary=synthesis,
        thread_id=thread_id
    )


@router.post("/opportunities/{opportunity_id}/ai/chat", response_model=AIChatResponse)
async def chat_with_opportunity(
    opportunity_id: str,
    request: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Envía un mensaje libre al thread de IA de la oportunidad.
    El modelo responde con el contexto completo de la oportunidad en memoria.

    Ejemplos de preguntas útiles:
    - '¿Qué objeción anticipas?'
    - '¿Cómo abordar la próxima reunión?'
    - '¿Qué riesgos ves en esta oportunidad?'
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El mensaje no puede estar vacío")

    try:
        ai = get_ai_provider()
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    # Construir contexto completo para que el chat tenga memoria de la oportunidad
    try:
        opp, account, contacts, activities, tasks = _build_context_for_opportunity(opportunity_id, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AI] Error building chat context for {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error al cargar contexto: {str(e)}")

    if not opp.chatgpt_thread_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta oportunidad no tiene un thread de IA. Usa 'Analizar con IA' primero."
        )

    try:
        context = build_opportunity_context(opp, account, contacts, activities, tasks)
    except Exception as e:
        logger.error(f"[AI] Error building chat prompt for {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error al construir el prompt: {str(e)}")

    try:
        response = ai.chat(request.message.strip(), thread_id=opp.chatgpt_thread_id, context=context)
    except Exception as e:
        logger.error(f"[AI] Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI provider error: {str(e)}")

    return AIChatResponse(response=response, thread_id=opp.chatgpt_thread_id)


@router.get("/opportunities/{opportunity_id}/ai/history", response_model=AIHistoryResponse)
async def get_ai_history(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Recupera el historial de mensajes del thread de IA de una oportunidad.
    Solo disponible cuando se usa Assistants API (thread_id empieza por 'thread_').
    """
    opp = _get_opportunity_or_404(opportunity_id, db)

    if not opp.chatgpt_thread_id:
        return AIHistoryResponse(thread_id="", messages=[])

    try:
        ai = get_ai_provider()
        messages = ai.get_thread_messages(opp.chatgpt_thread_id)
    except Exception as e:
        logger.warning(f"[AI] History error: {e}")
        messages = []

    return AIHistoryResponse(
        thread_id=opp.chatgpt_thread_id,
        messages=[AIHistoryMessage(**m) for m in messages]
    )
