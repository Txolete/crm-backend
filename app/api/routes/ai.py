"""
AI Integration endpoints — Sprint 4E / Sprint 5A

POST /opportunities/{id}/ai/analyze        — genera/actualiza síntesis ejecutiva (agente único)
POST /opportunities/{id}/ai/analyze-multi  — Sprint 5A: tres agentes en paralelo
POST /opportunities/{id}/ai/chat           — mensaje libre al thread de la oportunidad
GET  /opportunities/{id}/ai/history        — historial del thread
POST /opportunities/{id}/ai/feedback       — Sprint 5D: feedback de retrospectiva al cierre
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

class AITaskProposal(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None   # high | medium | low
    due_days: Optional[int] = None   # días desde hoy


class AIProbabilitySuggestion(BaseModel):
    percentage: Optional[int] = None
    justification: Optional[str] = None


class AIAnalyzeResponse(BaseModel):
    executive_summary: str
    next_strategic_action: str
    task_proposal: AITaskProposal
    probability_suggestion: AIProbabilitySuggestion
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
    created_at: Optional[str] = None


class AIHistoryResponse(BaseModel):
    thread_id: str
    messages: list[AIHistoryMessage]


class AIContextResponse(BaseModel):
    context: str


# Sprint 5A — Multi-agent
class AIAgentResult(BaseModel):
    analysis: str
    thread_id: str


class AIMultiAgentResponse(BaseModel):
    client: AIAgentResult
    sales: AIAgentResult
    memory: AIAgentResult
    task_proposal: Optional[dict] = None
    probability_suggestion: Optional[dict] = None
    message: str = "Análisis multi-agente completado"


# Sprint 5D — Feedback de retrospectiva
class AIFeedbackRequest(BaseModel):
    outcome_id: str                       # ID del registro en opportunity_outcomes
    what_worked: Optional[str] = None
    what_failed: Optional[str] = None
    ai_useful: Optional[str] = None       # 'yes' | 'no' | 'partial'
    notes: Optional[str] = None


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
        synthesis, next_action, task_proposal, probability_suggestion, thread_id = ai.analyze_opportunity(
            context, thread_id=opp.chatgpt_thread_id
        )
    except Exception as e:
        logger.error(f"[AI] Provider error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI provider error: {str(e)}"
        )

    # Guardar síntesis, próxima acción y thread_id en BD
    opp.executive_summary = synthesis
    opp.next_strategic_action = next_action
    opp.chatgpt_thread_id = thread_id
    opp.updated_at = get_utc_now()
    db.commit()

    logger.info(f"[AI] Opportunity {opportunity_id} analyzed. Thread: {thread_id}")

    return AIAnalyzeResponse(
        executive_summary=synthesis,
        next_strategic_action=next_action,
        task_proposal=AITaskProposal(**task_proposal) if task_proposal else AITaskProposal(),
        probability_suggestion=AIProbabilitySuggestion(**probability_suggestion) if probability_suggestion else AIProbabilitySuggestion(),
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
        response_text = ai.chat(request.message.strip(), thread_id=opp.chatgpt_thread_id, context=context)
    except Exception as e:
        logger.error(f"[AI] Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI provider error: {str(e)}")

    # Guardar Q&A en historial de BD
    import json
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        history = json.loads(opp.ai_chat_history) if opp.ai_chat_history else []
    except Exception:
        history = []
    history.append({"role": "user", "content": request.message.strip(), "created_at": now_iso})
    history.append({"role": "assistant", "content": response_text, "created_at": now_iso})
    opp.ai_chat_history = json.dumps(history, ensure_ascii=False)
    opp.updated_at = get_utc_now()
    db.commit()

    return AIChatResponse(response=response_text, thread_id=opp.chatgpt_thread_id)


@router.get("/opportunities/{opportunity_id}/ai/history", response_model=AIHistoryResponse)
async def get_ai_history(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Recupera el historial de Q&A del mini-chat guardado en BD.
    """
    import json
    opp = _get_opportunity_or_404(opportunity_id, db)

    try:
        messages = json.loads(opp.ai_chat_history) if opp.ai_chat_history else []
    except Exception:
        messages = []

    return AIHistoryResponse(
        thread_id=opp.chatgpt_thread_id or "",
        messages=[AIHistoryMessage(**m) for m in messages]
    )


@router.post("/opportunities/{opportunity_id}/ai/analyze-multi", response_model=AIMultiAgentResponse)
async def analyze_multi_agent(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Sprint 5A — Ejecuta los tres agentes especializados en paralelo.
    Devuelve tres perspectivas: Cliente, Comercial y Memoria Corporativa.
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
        logger.error(f"[AI-Multi] Error building context for {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al cargar contexto: {str(e)}")

    try:
        context = build_opportunity_context(opp, account, contacts, activities, tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al construir el prompt: {str(e)}")

    # Cargar histórico de oportunidades similares cerradas para el agente Memoria
    historical_context = _build_historical_context(opportunity_id, opp, db)

    # Recuperar thread IDs previos de los tres agentes (guardados en BD como JSON)
    import json
    try:
        agent_threads = json.loads(opp.chatgpt_thread_id) if (
            opp.chatgpt_thread_id and opp.chatgpt_thread_id.startswith("{")
        ) else {}
    except Exception:
        agent_threads = {}

    # Cargar prompts desde BD (fallback a constantes hardcoded si no existen)
    from app.models.config import CfgAiPrompt
    from app.utils.ai_service import SYSTEM_PROMPT_CLIENT, SYSTEM_PROMPT_SALES, SYSTEM_PROMPT_MEMORY
    prompt_rows = {r.agent: r.system_prompt for r in db.query(CfgAiPrompt).all()}
    prompts = {
        "client": prompt_rows.get("client") or SYSTEM_PROMPT_CLIENT,
        "sales":  prompt_rows.get("sales")  or SYSTEM_PROMPT_SALES,
        "memory": prompt_rows.get("memory") or SYSTEM_PROMPT_MEMORY,
    }

    logger.info(f"[AI-Multi] Analyzing opportunity {opportunity_id} with 3 agents")

    try:
        results = ai.analyze_multi_agent(context, historical_context=historical_context, thread_ids=agent_threads, prompts=prompts)
    except Exception as e:
        logger.error(f"[AI-Multi] Provider error: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"AI provider error: {str(e)}")

    # Guardar thread IDs de los tres agentes en chatgpt_thread_id (como JSON)
    new_threads = {
        "client": results["client"]["thread_id"],
        "sales":  results["sales"]["thread_id"],
        "memory": results["memory"]["thread_id"],
    }
    opp.chatgpt_thread_id = json.dumps(new_threads)
    opp.updated_at = get_utc_now()
    db.commit()

    logger.info(f"[AI-Multi] Opportunity {opportunity_id} analyzed by 3 agents.")

    # Extraer propuesta de tarea y sugerencia de probabilidad del agente Comercial
    from app.utils.ai_service import _parse_analysis_response
    try:
        _, next_action, task_proposal, probability_suggestion = _parse_analysis_response(
            results["sales"]["analysis"]
        )
    except Exception:
        task_proposal = {}
        probability_suggestion = {}

    return AIMultiAgentResponse(
        client=AIAgentResult(**results["client"]),
        sales=AIAgentResult(**results["sales"]),
        memory=AIAgentResult(**results["memory"]),
        task_proposal=task_proposal or {},
        probability_suggestion=probability_suggestion or {},
    )


def _build_historical_context(opportunity_id: str, opp, db: Session) -> Optional[str]:
    """
    Construye un resumen de oportunidades similares cerradas para el agente Memoria.
    Busca por tipo de oportunidad o por rango de valor similar.
    """
    try:
        from app.models.opportunity import OpportunityOutcome
        from app.models.config import CfgLostReason

        query = db.query(OpportunityOutcome).filter(
            OpportunityOutcome.opportunity_id != opportunity_id
        )

        # Filtrar por tipo similar si existe
        if opp.opportunity_type_id:
            from app.models.config import CfgOpportunityType
            ot = db.query(CfgOpportunityType).filter(
                CfgOpportunityType.id == opp.opportunity_type_id
            ).first()
            if ot:
                query = query.filter(OpportunityOutcome.opportunity_type == ot.name)

        outcomes = query.order_by(OpportunityOutcome.created_at.desc()).limit(10).all()

        if not outcomes:
            return None

        lines = [f"Se encontraron {len(outcomes)} oportunidades similares cerradas:\n"]
        for o in outcomes:
            result_label = "GANADA" if o.outcome == "won" else "PERDIDA"
            lines.append(
                f"- [{result_label}] {o.opportunity_name or 'Sin nombre'} "
                f"({o.account_name or '?'}) — "
                f"Valor: {o.final_value_eur:,.0f}€ — "
                f"Stage cierre: {o.stage_at_close or '?'} — "
                f"Días en pipeline: {o.days_in_pipeline or '?'}"
            )
            if o.outcome == "lost" and o.lost_reason_detail:
                lines.append(f"  Motivo pérdida: {o.lost_reason_detail}")
            if o.retro_what_worked:
                lines.append(f"  Qué funcionó: {o.retro_what_worked}")
            if o.retro_what_failed:
                lines.append(f"  Qué falló: {o.retro_what_failed}")

        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"[AI-Multi] Error building historical context: {e}")
        return None


@router.post("/opportunities/{opportunity_id}/ai/feedback")
async def save_ai_feedback(
    opportunity_id: str,
    request: AIFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Sprint 5D — Guarda el feedback de retrospectiva en opportunity_outcomes.
    Se llama desde el modal de cierre de oportunidad.
    """
    from app.models.opportunity import OpportunityOutcome

    outcome = db.query(OpportunityOutcome).filter(
        OpportunityOutcome.id == request.outcome_id
    ).first()

    if not outcome:
        raise HTTPException(status_code=404, detail="Outcome record not found")

    # Verificar que pertenece a esta oportunidad
    if outcome.opportunity_id != opportunity_id:
        raise HTTPException(status_code=403, detail="Outcome does not belong to this opportunity")

    outcome.retro_what_worked = request.what_worked
    outcome.retro_what_failed = request.what_failed
    outcome.retro_ai_useful = request.ai_useful
    outcome.retro_notes = request.notes
    db.commit()

    logger.info(f"[AI] Feedback saved for outcome {request.outcome_id} (opp {opportunity_id})")
    return {"message": "Feedback guardado", "outcome_id": request.outcome_id}


class AIAgentsAnalysisRequest(BaseModel):
    client: str = ""
    sales: str = ""
    memory: str = ""


class AIAgentsAnalysisResponse(BaseModel):
    client: str = ""
    sales: str = ""
    memory: str = ""
    analyzed_at: Optional[str] = None


@router.post("/opportunities/{opportunity_id}/ai/agents-analysis")
async def save_agents_analysis(
    opportunity_id: str,
    request: AIAgentsAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Sprint 5A — Persiste el último análisis multi-agente en ai_chat_history.
    Guarda una entrada especial de tipo 'agents' con los tres análisis como JSON.
    """
    import json
    from datetime import datetime, timezone

    opp = _get_opportunity_or_404(opportunity_id, db)

    # Leer historial actual, quitar entrada agents previa si existe, añadir la nueva
    try:
        history = json.loads(opp.ai_chat_history) if opp.ai_chat_history else []
    except Exception:
        history = []

    history = [h for h in history if h.get("role") != "agents"]  # eliminar anterior
    history.append({
        "role": "agents",
        "content": json.dumps({
            "client": request.client,
            "sales": request.sales,
            "memory": request.memory
        }, ensure_ascii=False),
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    opp.ai_chat_history = json.dumps(history, ensure_ascii=False)
    opp.updated_at = get_utc_now()
    db.commit()
    return {"message": "Análisis guardado"}


@router.get("/opportunities/{opportunity_id}/ai/agents-analysis", response_model=AIAgentsAnalysisResponse)
async def get_agents_analysis(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Sprint 5A — Devuelve el último análisis multi-agente guardado.
    """
    import json

    opp = _get_opportunity_or_404(opportunity_id, db)

    try:
        history = json.loads(opp.ai_chat_history) if opp.ai_chat_history else []
    except Exception:
        history = []

    # Buscar la última entrada de tipo 'agents'
    agents_entry = next((h for h in reversed(history) if h.get("role") == "agents"), None)
    if not agents_entry:
        return AIAgentsAnalysisResponse()

    try:
        content = json.loads(agents_entry["content"])
    except Exception:
        return AIAgentsAnalysisResponse()

    return AIAgentsAnalysisResponse(
        client=content.get("client", ""),
        sales=content.get("sales", ""),
        memory=content.get("memory", ""),
        analyzed_at=agents_entry.get("created_at")
    )


@router.post("/opportunities/{opportunity_id}/ai/ensure-outcome")
async def ensure_opportunity_outcome(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Crea un registro opportunity_outcomes para una oportunidad cerrada que no lo tiene.
    Usado para añadir retrospectiva a oportunidades cerradas antes de Sprint 5.
    Devuelve el outcome_id (existente o recién creado).
    """
    from app.models.opportunity import OpportunityOutcome, Task, Activity as ActModel
    from app.models.account import Account as AccountModel
    from app.models.config import CfgStage, CfgOpportunityType, CfgClientMentalState, CfgStageProbability, CfgLostReason
    from app.utils.audit import generate_id
    from datetime import datetime, timezone

    opp = _get_opportunity_or_404(opportunity_id, db)

    if opp.close_outcome not in ('won', 'lost'):
        raise HTTPException(status_code=400, detail="La oportunidad no está cerrada")

    # Si ya existe un outcome, devolverlo
    existing = db.query(OpportunityOutcome).filter(
        OpportunityOutcome.opportunity_id == opportunity_id
    ).first()
    if existing:
        has_retro = bool(existing.retro_what_worked or existing.retro_what_failed or existing.retro_notes)
        return {"outcome_id": existing.id, "created": False, "has_retro": has_retro}

    # Crear snapshot retroactivo
    account = db.query(AccountModel).filter(AccountModel.id == opp.account_id).first()
    stage = db.query(CfgStage).filter(CfgStage.id == opp.stage_id).first()

    opp_type_name = None
    if opp.opportunity_type_id:
        ot = db.query(CfgOpportunityType).filter(CfgOpportunityType.id == opp.opportunity_type_id).first()
        opp_type_name = ot.name if ot else None

    mental_state_name = None
    if opp.client_mental_state_id:
        ms = db.query(CfgClientMentalState).filter(CfgClientMentalState.id == opp.client_mental_state_id).first()
        mental_state_name = ms.name if ms else None

    activity_count = db.query(ActModel).filter(ActModel.opportunity_id == opportunity_id).count()
    task_count = db.query(Task).filter(Task.opportunity_id == opportunity_id).count()

    final_prob = opp.probability_override
    if final_prob is None:
        sp = db.query(CfgStageProbability).filter(CfgStageProbability.stage_id == opp.stage_id).first()
        final_prob = sp.probability if sp else None

    days_in_pipeline = None
    if opp.created_at and opp.close_date:
        try:
            close = opp.close_date.date() if hasattr(opp.close_date, 'date') else opp.close_date
            created = opp.created_at.date() if hasattr(opp.created_at, 'date') else opp.created_at
            days_in_pipeline = (close - created).days
        except Exception:
            pass

    outcome = OpportunityOutcome(
        id=generate_id(),
        opportunity_id=opportunity_id,
        outcome=opp.close_outcome,
        close_date=opp.close_date,
        final_value_eur=opp.won_value_eur if opp.close_outcome == 'won' else opp.expected_value_eur,
        lost_reason_id=opp.lost_reason_id,
        lost_reason_detail=opp.lost_reason_detail,
        account_name=account.name if account else None,
        opportunity_name=opp.name,
        opportunity_type=opp_type_name,
        stage_at_close=stage.name if stage else opp.close_outcome,
        days_in_pipeline=days_in_pipeline,
        activity_count=activity_count,
        task_count=task_count,
        final_probability=final_prob,
        client_mental_state=mental_state_name,
        strategic_objective=opp.strategic_objective,
        executive_summary_at_close=opp.executive_summary,
        owner_user_id=opp.owner_user_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(outcome)
    db.commit()
    logger.info(f"[AI] Retroactive outcome created for {opportunity_id} ({opp.close_outcome})")
    return {"outcome_id": outcome.id, "created": True}


@router.get("/opportunities/{opportunity_id}/ai/context", response_model=AIContextResponse)
async def get_ai_context(
    opportunity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Devuelve el contexto Markdown completo de la oportunidad (sin llamar a OpenAI).
    Usado por el botón 'Copiar contexto' para pegar en ChatGPT Pro / Claude web.
    """
    try:
        opp, account, contacts, activities, tasks = _build_context_for_opportunity(opportunity_id, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[AI] Error building context for {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error al construir contexto: {str(e)}")

    try:
        context = build_opportunity_context(opp, account, contacts, activities, tasks)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Error al generar el Markdown: {str(e)}")

    return AIContextResponse(context=context)
