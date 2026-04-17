"""
AI Service Layer — Sprint 4E / Sprint 5A
Interfaz abstracta intercambiable entre providers de IA.

Providers disponibles:
  - OpenAIProvider (por defecto) — usa Chat Completions o Assistants API
  - Futuro: AnthropicProvider, LocalLLMProvider

Sprint 5A — Tres agentes especializados:
  - AGENT_CLIENT: perspectiva del comprador
  - AGENT_SALES: táctica y siguiente movimiento del vendedor
  - AGENT_MEMORY: patrones del histórico de oportunidades cerradas

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
# SYSTEM PROMPTS — Tres agentes Sprint 5A
# ============================================================================

SYSTEM_PROMPT_CLIENT = """Eres el agente "Cliente" de un CRM B2B del sector energético en España.
Tu única perspectiva es la del COMPRADOR: el cliente potencial.

Cuando recibas el contexto de una oportunidad:
1. Analiza qué está pensando realmente el cliente en este momento
2. Identifica las objeciones que NO ha dicho en voz alta (miedos, dudas, bloqueos internos)
3. Detecta qué le frenaría de tomar una decisión ahora mismo
4. Señala qué necesitaría ver u oír para avanzar con confianza
5. Si hay estado mental del cliente definido, úsalo como punto de partida

Responde SOLO desde la perspectiva del cliente. No des consejos al vendedor.
Sé directo, psicológico y basado en los datos del contexto.
Responde siempre en español. Máximo 5-6 líneas."""

SYSTEM_PROMPT_SALES = """Eres el agente "Comercial" de un CRM B2B del sector energético en España.
Eres un vendedor experto con 15 años de experiencia en ventas B2B energéticas.

Cuando recibas el contexto de una oportunidad responde SIEMPRE con esta estructura exacta:

SÍNTESIS:
[2-3 frases: diagnóstico del estado actual de la oportunidad desde perspectiva comercial]

PRÓXIMA ACCIÓN:
[1 frase concreta: el movimiento más efectivo ahora mismo]

TAREA PROPUESTA:
- Título: [título breve de la tarea]
- Descripción: [descripción de la tarea]
- Prioridad: [Alta / Media / Baja]
- Plazo: [número] días

PROBABILIDAD SUGERIDA:
- Porcentaje: [número entre 0 y 100]%
- Justificación: [1 frase explicando el porcentaje]

Sé directo, táctico y crítico si es necesario — el objetivo es ganar. Responde siempre en español."""

SYSTEM_PROMPT_MEMORY = """Eres el agente "Memoria Corporativa" de un CRM B2B del sector energético en España.
Tu función es detectar patrones en el historial de oportunidades cerradas y aplicarlos a la oportunidad actual.

Cuando recibas el contexto de una oportunidad y el histórico de casos similares:
1. Identifica patrones de éxito y fracaso en oportunidades similares (sector, valor, stage, tipo)
2. Compara el comportamiento actual con los casos ganados: ¿qué tienen en común?
3. Compara con los casos perdidos: ¿hay señales de alerta presentes aquí también?
4. Estima una probabilidad real basada en el histórico (no en la configurada en el CRM)
5. Si no hay suficientes datos históricos, indícalo claramente

Responde con datos concretos del histórico si los tienes, o con patrones generales del sector si no.
Responde siempre en español. Máximo 6-7 líneas."""


# ============================================================================
# INTERFAZ ABSTRACTA
# ============================================================================

class AIProvider(ABC):
    """Contrato que todo provider de IA debe cumplir."""

    @abstractmethod
    def analyze_multi_agent(
        self,
        context: str,
        historical_context: Optional[str] = None,
        thread_ids: Optional[dict] = None
    ) -> dict:
        """
        Sprint 5A — Ejecuta los tres agentes especializados.

        Args:
            context: Markdown completo de la oportunidad
            historical_context: Resumen de oportunidades similares cerradas (para agente Memoria)
            thread_ids: {"client": str, "sales": str, "memory": str} — thread IDs previos

        Returns:
            {
                "client":  {"analysis": str, "thread_id": str},
                "sales":   {"analysis": str, "thread_id": str},
                "memory":  {"analysis": str, "thread_id": str},
            }
        """
        ...

    @abstractmethod
    def analyze_opportunity(self, context: str, thread_id: Optional[str] = None) -> tuple:
        """
        Envía el contexto de una oportunidad al modelo.

        Returns:
            (síntesis: str, next_action: str, task_proposal: dict, probability_suggestion: dict, thread_id: str)
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

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        assistant_id: str = "",
        agent_client_id: str = "",
        agent_sales_id: str = "",
        agent_memory_id: str = "",
    ):
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)
            self._model = model
            self._assistant_id = assistant_id or None
            # Sprint 5A — IDs de los tres agentes especializados (vacío = usar Chat Completions)
            self._agent_client_id = agent_client_id or ""
            self._agent_sales_id = agent_sales_id or ""
            self._agent_memory_id = agent_memory_id or ""
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai>=1.30.0")

    def analyze_multi_agent(
        self,
        context: str,
        historical_context: Optional[str] = None,
        thread_ids: Optional[dict] = None
    ) -> dict:
        """
        Sprint 5A — Ejecuta los tres agentes en secuencia y devuelve sus análisis.
        (En producción se pueden ejecutar en paralelo con asyncio; aquí secuencial para simplicidad.)
        """
        thread_ids = thread_ids or {}

        agents = [
            ("client",  SYSTEM_PROMPT_CLIENT,  self._agent_client_id),
            ("sales",   SYSTEM_PROMPT_SALES,   self._agent_sales_id),
            ("memory",  SYSTEM_PROMPT_MEMORY,  self._agent_memory_id),
        ]

        results = {}
        for agent_key, system_prompt, assistant_id in agents:
            thread_id = thread_ids.get(agent_key)
            # El agente de Memoria recibe también el histórico si existe
            ctx = context
            if agent_key == "memory" and historical_context:
                ctx = context + "\n\n## Histórico de oportunidades similares cerradas\n" + historical_context

            try:
                if assistant_id and assistant_id.startswith("asst_"):
                    analysis, new_thread_id = self._run_agent_with_assistant(
                        ctx, assistant_id, thread_id
                    )
                else:
                    analysis, new_thread_id = self._run_agent_with_chat(
                        ctx, system_prompt, thread_id
                    )
                results[agent_key] = {"analysis": analysis, "thread_id": new_thread_id or ""}
            except Exception as e:
                logger.error(f"[AI] Agent '{agent_key}' error: {e}")
                results[agent_key] = {"analysis": f"[Error en agente {agent_key}: {e}]", "thread_id": ""}

        return results

    def _run_agent_with_chat(self, context: str, system_prompt: str, thread_id: Optional[str]) -> tuple[str, str]:
        """Ejecuta un agente usando Chat Completions."""
        import hashlib
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analiza esta oportunidad:\n\n{context}"}
            ],
            temperature=0.4,
            max_completion_tokens=600
        )
        analysis = response.choices[0].message.content.strip()
        synthetic_id = thread_id or f"chat_{hashlib.md5(context[:80].encode()).hexdigest()[:16]}"
        return analysis, synthetic_id

    def _run_agent_with_assistant(self, context: str, assistant_id: str, thread_id: Optional[str]) -> tuple[str, str]:
        """Ejecuta un agente usando Assistants API."""
        if thread_id and thread_id.startswith("thread_"):
            thread = self._client.beta.threads.retrieve(thread_id)
        else:
            thread = self._client.beta.threads.create()

        self._client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Analiza esta oportunidad:\n\n{context}"
        )
        run = self._client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant_id,
            timeout=30
        )
        if run.status != "completed":
            raise RuntimeError(f"Assistant run failed: {run.status}")
        messages = self._client.beta.threads.messages.list(thread_id=thread.id, limit=1)
        analysis = messages.data[0].content[0].text.value.strip()
        return analysis, thread.id

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

    def _analyze_with_chat(self, context: str, thread_id: Optional[str]) -> tuple[str, str, str]:
        """Usa Chat Completions API. Devuelve síntesis, próxima acción, tarea propuesta y probabilidad."""
        prompt = f"""Analiza la siguiente oportunidad comercial y responde con este formato EXACTO (respeta todos los marcadores):

SÍNTESIS:
[4-5 líneas: situación actual, momentum de la relación, riesgos principales]

PRÓXIMA ACCIÓN:
[1 acción estratégica concreta y accionable. Máximo 2 líneas.]

TAREA PROPUESTA:
Título: [título corto y accionable para la tarea, máximo 80 caracteres]
Descripción: [qué hay que hacer exactamente y qué se busca conseguir. 1-3 frases.]
Prioridad: [alta|media|baja]
Días hasta vencimiento: [número entero, ej: 7]

PROBABILIDAD SUGERIDA:
Porcentaje: [número entre 0 y 100]
Justificación: [1 línea explicando por qué ese porcentaje]

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
            max_completion_tokens=900
        )
        raw = response.choices[0].message.content.strip()

        synthesis, next_action, task_proposal, probability_suggestion = _parse_analysis_response(raw)

        import hashlib
        synthetic_thread_id = thread_id or f"chat_{hashlib.md5(context[:100].encode()).hexdigest()[:16]}"
        return synthesis, next_action, task_proposal, probability_suggestion, synthetic_thread_id

    def _analyze_with_assistant(self, context: str, thread_id: Optional[str]) -> tuple[str, str, str]:
        """Usa Assistants API con threads persistentes."""
        if thread_id and thread_id.startswith("thread_"):
            thread = self._client.beta.threads.retrieve(thread_id)
        else:
            thread = self._client.beta.threads.create()

        prompt = f"""Analiza esta oportunidad y responde con este formato EXACTO:

SÍNTESIS:
[4-5 líneas de síntesis ejecutiva]

PRÓXIMA ACCIÓN:
[1 acción concreta y accionable. Máximo 2 líneas.]

--- CONTEXTO ---
{context}"""

        self._client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )

        run = self._client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=self._assistant_id,
            timeout=30
        )

        if run.status != "completed":
            raise RuntimeError(f"Assistant run failed with status: {run.status}")

        messages = self._client.beta.threads.messages.list(thread_id=thread.id, limit=1)
        raw = messages.data[0].content[0].text.value.strip()
        synthesis, next_action, task_proposal, probability_suggestion = _parse_analysis_response(raw)
        return synthesis, next_action, task_proposal, probability_suggestion, thread.id

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
                    max_completion_tokens=500
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
# PARSER — extrae bloques estructurados de la respuesta IA
# ============================================================================

def _parse_analysis_response(raw: str) -> tuple:
    """
    Parsea la respuesta estructurada del modelo en 4 bloques:
    SÍNTESIS / PRÓXIMA ACCIÓN / TAREA PROPUESTA / PROBABILIDAD SUGERIDA

    Returns:
        (synthesis: str, next_action: str, task_proposal: dict, probability_suggestion: dict)
    """
    import re

    def extract_block(text: str, marker: str) -> str:
        """Extrae el contenido entre un marcador y el siguiente marcador o fin de texto."""
        # Buscar el marcador (case-insensitive)
        m = re.search(marker, text, re.IGNORECASE)
        if not m:
            return ''
        start = m.end()
        # Buscar el siguiente marcador principal
        next_markers = [
            r'S[IÍ]NTESIS\s*:',
            r'PR[OÓ]XIMA\s+ACCI[OÓ]N\s*:',
            r'TAREA\s+PROPUESTA\s*:',
            r'PROBABILIDAD\s+SUGERIDA\s*:',
        ]
        end = len(text)
        for nm in next_markers:
            nm2 = re.search(nm, text[start:], re.IGNORECASE)
            if nm2:
                candidate = start + nm2.start()
                if candidate < end:
                    end = candidate
        return text[start:end].strip()

    synthesis    = extract_block(raw, r'S[IÍ]NTESIS\s*:') or raw
    next_action  = extract_block(raw, r'PR[OÓ]XIMA\s+ACCI[OÓ]N\s*:')
    task_raw     = extract_block(raw, r'TAREA\s+PROPUESTA\s*:')
    prob_raw     = extract_block(raw, r'PROBABILIDAD\s+SUGERIDA\s*:')

    # Parsear TAREA PROPUESTA en dict
    task_proposal: dict = {}
    if task_raw:
        for line in task_raw.splitlines():
            if ':' in line:
                k, _, v = line.partition(':')
                k_low = k.strip().lower()
                v = v.strip()
                if 'tulo' in k_low or 'titulo' in k_low:
                    task_proposal['title'] = v
                elif 'escripci' in k_low:
                    task_proposal['description'] = v
                elif 'rioridad' in k_low:
                    p = v.lower()
                    task_proposal['priority'] = 'high' if 'alt' in p else ('low' if 'baj' in p else 'medium')
                elif 'as' in k_low and ('venc' in k_low or 'día' in k_low or 'dia' in k_low):
                    try:
                        task_proposal['due_days'] = int(re.search(r'\d+', v).group())
                    except Exception:
                        task_proposal['due_days'] = 7

    # Parsear PROBABILIDAD SUGERIDA en dict
    probability_suggestion: dict = {}
    if prob_raw:
        for line in prob_raw.splitlines():
            if ':' in line:
                k, _, v = line.partition(':')
                k_low = k.strip().lower()
                v = v.strip()
                if 'porcentaje' in k_low or 'porcent' in k_low:
                    try:
                        num = re.search(r'\d+', v)
                        probability_suggestion['percentage'] = int(num.group()) if num else None
                    except Exception:
                        pass
                elif 'justif' in k_low:
                    probability_suggestion['justification'] = v
        # Fallback: buscar número % en el bloque completo
        if 'percentage' not in probability_suggestion:
            m = re.search(r'(\d{1,3})\s*%', prob_raw)
            if m:
                probability_suggestion['percentage'] = int(m.group(1))

    return synthesis, next_action, task_proposal, probability_suggestion


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

    # ── Conclusiones de sesión externa (ChatGPT Pro / Claude / etc.) ─────────
    external_notes = getattr(opportunity, 'external_session_notes', None)
    if external_notes:
        lines.append("## Conclusiones de sesión externa (análisis profundo previo)")
        lines.append(external_notes)
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
            assistant_id=settings.openai_assistant_id,
            agent_client_id=settings.openai_agent_client_id,
            agent_sales_id=settings.openai_agent_sales_id,
            agent_memory_id=settings.openai_agent_memory_id,
        )
    # Futuro: elif provider == "anthropic": return AnthropicProvider(...)
    # Futuro: elif provider == "local": return LocalLLMProvider(...)
    else:
        raise ValueError(f"Unknown AI provider: {provider}. Valid: openai")
