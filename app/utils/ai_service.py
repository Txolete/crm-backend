"""
AI Service Layer — Sprint 4E
Interfaz abstracta intercambiable entre providers de IA.

Providers disponibles:
  - OpenAIProvider (por defecto) — usa Threads API de OpenAI
  - Futuro: AnthropicProvider, LocalLLMProvider

Para cambiar de provider: solo cambiar AI_PROVIDER en .env.
El resto del código (endpoints, frontend, BD) no cambia nada.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================================
# INTERFAZ ABSTRACTA
# ============================================================================

class AIProvider(ABC):
    """Contrato que todo provider de IA debe cumplir."""

    @abstractmethod
    def analyze_opportunity(self, context: str, thread_id: Optional[str] = None) -> tuple[str, str]:
        """
        Envía el contexto de una oportunidad al modelo y devuelve la síntesis.

        Args:
            context: Markdown estructurado con todos los datos de la oportunidad
            thread_id: ID del thread previo (continúa conversación si existe)

        Returns:
            (síntesis: str, thread_id: str)
        """
        ...

    @abstractmethod
    def chat(self, message: str, thread_id: str, context: Optional[str] = None) -> str:
        """
        Envía un mensaje libre al thread existente de una oportunidad.

        Args:
            message: Pregunta o mensaje del comercial
            thread_id: ID del thread de la oportunidad
            context: Contexto completo de la oportunidad (Markdown). Se inyecta
                     en el system message para que el modelo siempre tenga la
                     información actualizada, aunque no haya threads persistentes.

        Returns:
            Respuesta del modelo
        """
        ...

    @abstractmethod
    def get_thread_messages(self, thread_id: str, limit: int = 10) -> list[dict]:
        """
        Recupera los últimos mensajes del thread.

        Returns:
            Lista de {"role": "user"|"assistant", "content": str, "created_at": int}
        """
        ...


# ============================================================================
# OPENAI PROVIDER
# ============================================================================

class OpenAIProvider(AIProvider):
    """
    Provider usando la API de OpenAI.
    Usa Threads para mantener historial persistente por oportunidad.
    """

    SYSTEM_PROMPT = """Eres un asistente comercial experto en ventas B2B del sector energético.
Tu rol es ayudar a los comerciales de ASICXXI a analizar sus oportunidades de venta,
identificar riesgos, sugerir próximas acciones y generar síntesis ejecutivas claras.

Cuando recibas el contexto de una oportunidad:
1. Analiza el estado actual (stage, valor, probabilidad, estado mental del cliente)
2. Identifica los stakeholders clave y su posición
3. Revisa la actividad reciente para entender el momentum
4. Genera una síntesis ejecutiva concisa (4-5 líneas máximo)
5. Sugiere la próxima acción estratégica más efectiva

Responde siempre en español. Sé directo y accionable."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", assistant_id: str = ""):
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)
            self._model = model
            self._assistant_id = assistant_id or None
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai>=1.30.0")

    def analyze_opportunity(self, context: str, thread_id: Optional[str] = None) -> tuple[str, str]:
        """Analiza una oportunidad y devuelve síntesis + thread_id."""
        try:
            if self._assistant_id:
                return self._analyze_with_assistant(context, thread_id)
            else:
                return self._analyze_with_chat(context, thread_id)
        except Exception as e:
            logger.error(f"[AI] analyze_opportunity error: {e}")
            raise

    def _analyze_with_chat(self, context: str, thread_id: Optional[str]) -> tuple[str, str]:
        """Usa Chat Completions API (sin Assistants)."""
        prompt = f"""Analiza la siguiente oportunidad comercial y genera:
1. Una síntesis ejecutiva (4-5 líneas)
2. La próxima acción estratégica recomendada

--- CONTEXTO DE LA OPORTUNIDAD ---
{context}
---"""

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=600
        )
        synthesis = response.choices[0].message.content.strip()

        # Sin Assistants API no hay thread real — generamos un ID sintético
        # para que la UI sepa que ya se analizó
        import hashlib
        synthetic_thread_id = thread_id or f"chat_{hashlib.md5(context[:100].encode()).hexdigest()[:16]}"
        return synthesis, synthetic_thread_id

    def _analyze_with_assistant(self, context: str, thread_id: Optional[str]) -> tuple[str, str]:
        """Usa Assistants API con threads persistentes."""
        # Crear o recuperar thread
        if thread_id and thread_id.startswith("thread_"):
            thread = self._client.beta.threads.retrieve(thread_id)
        else:
            thread = self._client.beta.threads.create()

        # Añadir mensaje con el contexto actualizado
        self._client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Analiza esta oportunidad y genera síntesis ejecutiva:\n\n{context}"
        )

        # Ejecutar el assistant
        run = self._client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=self._assistant_id,
            timeout=30
        )

        if run.status != "completed":
            raise RuntimeError(f"Assistant run failed with status: {run.status}")

        messages = self._client.beta.threads.messages.list(thread_id=thread.id, limit=1)
        synthesis = messages.data[0].content[0].text.value.strip()
        return synthesis, thread.id

    def chat(self, message: str, thread_id: str, context: Optional[str] = None) -> str:
        """Envía mensaje libre al thread, inyectando siempre el contexto de la oportunidad."""
        try:
            if self._assistant_id and thread_id.startswith("thread_"):
                return self._chat_with_assistant(message, thread_id)
            else:
                # Chat Completions: inyectamos el contexto en el system message
                # para que el modelo siempre sepa de qué oportunidad se habla
                system = self.SYSTEM_PROMPT
                if context:
                    system += f"\n\n---\nCONTEXTO ACTUAL DE LA OPORTUNIDAD (datos en tiempo real):\n\n{context}\n---"

                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": message}
                    ],
                    temperature=0.4,
                    max_tokens=500
                )
                return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"[AI] chat error: {e}")
            raise

    def _chat_with_assistant(self, message: str, thread_id: str) -> str:
        self._client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        run = self._client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=self._assistant_id,
            timeout=30
        )
        if run.status != "completed":
            raise RuntimeError(f"Assistant run failed: {run.status}")
        messages = self._client.beta.threads.messages.list(thread_id=thread_id, limit=1)
        return messages.data[0].content[0].text.value.strip()

    def get_thread_messages(self, thread_id: str, limit: int = 10) -> list[dict]:
        """Recupera mensajes del thread (solo con Assistants API)."""
        if not thread_id.startswith("thread_"):
            return []
        try:
            messages = self._client.beta.threads.messages.list(thread_id=thread_id, limit=limit)
            result = []
            for msg in reversed(messages.data):
                content = msg.content[0].text.value if msg.content else ""
                result.append({
                    "role": msg.role,
                    "content": content,
                    "created_at": msg.created_at
                })
            return result
        except Exception as e:
            logger.warning(f"[AI] get_thread_messages error: {e}")
            return []


# ============================================================================
# CONTEXT BUILDER — prompt interno
# ============================================================================

def build_opportunity_context(opportunity, account, contacts: list, activities: list, tasks: list) -> str:
    """
    Construye el Markdown estructurado de una oportunidad para enviar como
    contexto al modelo de IA. Incluye:
    - Ficha completa del cliente (cuenta)
    - Datos de la oportunidad y campos estratégicos IA
    - Stakeholders con canales de contacto
    - Timeline completo de actividades
    - Tareas pendientes y completadas
    """
    lines = []

    # ── Cabecera ─────────────────────────────────────────────────────────────
    opp_name = getattr(opportunity, 'name', None) or getattr(opportunity, 'account_name', 'Sin nombre')
    account_name = getattr(opportunity, 'account_name', '')
    lines.append(f"# Oportunidad: {opp_name}")
    lines.append("")

    # ── Ficha del cliente ─────────────────────────────────────────────────────
    lines.append("## Ficha del cliente")
    if account:
        lines.append(f"**Empresa:** {account.name}")
        if getattr(account, 'customer_type_name', None):
            lines.append(f"**Tipo de cliente:** {account.customer_type_name}")
        if getattr(account, 'region_name', None):
            lines.append(f"**Provincia:** {account.region_name}")
        if account.website:
            lines.append(f"**Web:** {account.website}")
        if account.email:
            lines.append(f"**Email:** {account.email}")
        if account.phone:
            lines.append(f"**Teléfono:** {account.phone}")
        if account.address:
            lines.append(f"**Dirección:** {account.address}")
        if account.tax_id:
            lines.append(f"**CIF/NIF:** {account.tax_id}")
        if account.notes:
            lines.append(f"**Notas del cliente:**")
            lines.append(account.notes)
    else:
        lines.append("Sin datos de cliente")
    lines.append("")

    # ── Datos de la oportunidad ───────────────────────────────────────────────
    lines.append("## Oportunidad")
    stage_name = getattr(opportunity, 'stage_name', '')
    value = getattr(opportunity, 'expected_value_eur', 0) or 0
    prob = getattr(opportunity, 'probability_override', None)
    stage_prob = getattr(opportunity, 'stage_probability', None)
    prob_display = f"{int((prob or stage_prob or 0) * 100)}%"
    owner = getattr(opportunity, 'owner_user_name', '') or ''
    close_month = getattr(opportunity, 'forecast_close_month', '') or ''
    opp_type = getattr(opportunity, 'opportunity_type_name', None)

    lines.append(f"**Stage:** {stage_name} | **Valor:** {value:,.0f}€ | **Probabilidad:** {prob_display}")
    lines.append(f"**Comercial responsable:** {owner} | **Cierre previsto:** {close_month}")
    if opp_type:
        lines.append(f"**Tipo de oportunidad:** {opp_type}")

    stage_detail = getattr(opportunity, 'stage_detail', None)
    if stage_detail:
        lines.append(f"**Detalle del stage:** {stage_detail}")
    lines.append("")

    # ── Estado mental del cliente ─────────────────────────────────────────────
    mental_state = getattr(opportunity, 'client_mental_state_name', None)
    lines.append("## Estado mental del cliente")
    lines.append(mental_state or "No definido")
    lines.append("")

    # ── Campos estratégicos ───────────────────────────────────────────────────
    strategic_obj = getattr(opportunity, 'strategic_objective', None)
    lines.append("## Objetivo estratégico de esta oportunidad")
    lines.append(strategic_obj or "No definido")
    lines.append("")

    next_action = getattr(opportunity, 'next_strategic_action', None)
    lines.append("## Próxima acción estratégica definida")
    lines.append(next_action or "No definida")
    lines.append("")

    # ── Síntesis previa ───────────────────────────────────────────────────────
    exec_summary = getattr(opportunity, 'executive_summary', None)
    if exec_summary:
        lines.append("## Síntesis ejecutiva anterior")
        lines.append(exec_summary)
        lines.append("")

    # ── Stakeholders ──────────────────────────────────────────────────────────
    lines.append("## Contactos / Stakeholders")
    if contacts:
        for c in contacts:
            full_name = f"{getattr(c, 'first_name', '') or ''} {getattr(c, 'last_name', '') or ''}".strip() or "Sin nombre"
            role = getattr(c, 'role_name', '') or getattr(c, 'contact_role_id', '') or ''
            email = ''
            phone = ''
            if hasattr(c, 'channels') and c.channels:
                for ch in c.channels:
                    if ch.type == 'email':
                        email = ch.value
                    elif ch.type == 'phone':
                        phone = ch.value
            parts = [full_name]
            if role:
                parts.append(f"({role})")
            if email:
                parts.append(email)
            if phone:
                parts.append(phone)
            lines.append(f"- {' — '.join(parts)}")
    else:
        lines.append("- Sin contactos registrados")
    lines.append("")

    # ── Timeline completo de actividades ──────────────────────────────────────
    lines.append(f"## Timeline de actividades ({len(activities)} registros, orden cronológico)")
    if activities:
        for act in activities:
            occurred = getattr(act, 'occurred_at', '')
            if hasattr(occurred, 'strftime'):
                occurred = occurred.strftime('%Y-%m-%d')
            act_type = getattr(act, 'type', '')
            summary = getattr(act, 'summary', '')
            lines.append(f"- {occurred} [{act_type}]: {summary}")
    else:
        lines.append("- Sin actividad registrada")
    lines.append("")

    # ── Tareas pendientes ─────────────────────────────────────────────────────
    open_tasks = [t for t in tasks if getattr(t, 'status', '') in ('open', 'in_progress')]
    lines.append(f"## Tareas pendientes ({len(open_tasks)})")
    if open_tasks:
        for t in open_tasks:
            due = getattr(t, 'due_date', '')
            if isinstance(due, date):
                due = due.strftime('%Y-%m-%d')
            priority = getattr(t, 'priority', '')
            desc = getattr(t, 'description', '') or ''
            line = f"- [ ] [{priority}] {t.title} — vence {due or 'sin fecha'}"
            if desc:
                line += f" | {desc}"
            lines.append(line)
    else:
        lines.append("- Sin tareas pendientes")
    lines.append("")

    # ── Tareas completadas ────────────────────────────────────────────────────
    done_tasks = [t for t in tasks if getattr(t, 'status', '') == 'completed']
    if done_tasks:
        lines.append(f"## Tareas completadas ({len(done_tasks)})")
        for t in done_tasks:
            completed = getattr(t, 'completed_at', '')
            if hasattr(completed, 'strftime'):
                completed = completed.strftime('%Y-%m-%d')
            lines.append(f"- [x] {t.title} — completada {completed or ''}")
        lines.append("")

    return "\n".join(lines)


# ============================================================================
# FACTORY — selecciona el provider según configuración
# ============================================================================

def get_ai_provider() -> AIProvider:
    """
    Devuelve la instancia del provider configurado en .env (AI_PROVIDER).
    Para cambiar de OpenAI a Anthropic o modelo propio:
      1. Implementar la clase correspondiente heredando de AIProvider
      2. Cambiar AI_PROVIDER en .env
    """
    from app.config import get_settings
    settings = get_settings()

    if not settings.ai_enabled:
        raise RuntimeError("AI integration is disabled (AI_ENABLED=false)")

    if not settings.openai_api_key and settings.ai_provider == "openai":
        raise RuntimeError("OPENAI_API_KEY is not configured. Add it to .env")

    provider = settings.ai_provider.lower()

    if provider == "openai":
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            assistant_id=settings.openai_assistant_id
        )
    # Futuro: elif provider == "anthropic": return AnthropicProvider(...)
    # Futuro: elif provider == "local": return LocalLLMProvider(...)
    else:
        raise ValueError(f"Unknown AI provider: {provider}. Valid: openai")
