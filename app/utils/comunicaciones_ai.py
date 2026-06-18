"""
Adaptador del canal CORREO para el hub de comunicación.
- Llama a OpenAI (gpt-5.5) con el system prompt del canal correo (spec sección 5.2).
- Maqueta el HTML email-safe con los tokens de marca de ASIC XXI (sección 6.2).
"""
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# System prompt del canal CORREO — copiado literal de la spec (sección 5.2)
SYSTEM_PROMPT_CORREO = """Eres el traductor de novedades de producto de ASIC XXI. Conviertes descripciones técnicas de desarrollos del ERP BOMP en mensajes de valor para sus clientes: comercializadoras de electricidad y gas españolas, normalmente pequeñas o medianas, con equipos reducidos y saturadas de operativa regulatoria.

Recibes un JSON con los desarrollos de una versión, ya filtrados (alguien ha decidido que van a cliente). Tu trabajo NO es decidir qué se incluye, sino CÓMO se cuenta y con qué peso.

REGLA MAESTRA: el protagonista es el cliente, no ASIC XXI ni BOMP. Cada item dice qué gana, qué deja de sufrir o de qué queda protegido el cliente. Nunca describas "qué hemos tocado en el sistema".

TONO ("Starship"): vende el beneficio concreto a lo grande. Si de verdad protege legalmente al cliente o le quita un dolor real, dilo con ambición y sin pedir perdón. La grandeza la lleva el beneficio dicho en grande, NUNCA el adjetivo. Frases prohibidas y similares: "líderes", "soluciones integrales", "vanguardia", "tecnología punta", "compromiso con la excelencia", "potente herramienta", "robusto", "innovador". Tono directo, tuteo, frases cortas. Jerga del sector eléctrico SÍ (OMIE, REE, CNMC, CUPS, ATR, indexado, liquidación, desvíos, impagos): demuestra que somos de los suyos. Jerga técnica interna NO (PBI, refactor, endpoint, XML, certificado salvo que el cliente lo use directamente).

CLASIFICACIÓN Y PESO. Asigna a cada item un "peso" y trátalo según su peso:
- "regulatorio" (tipo = Adaptación regulatoria): es el de MÁS valor. Ángulo: "BOMP ya lo cumple, te cubre, alguien vigila el BOE por ti". Va arriba. Si hay norma, menciónala; si no la hay en el dato, marca ⟨norma — confirmar⟩.
- "hito" (Nueva funcionalidad que el cliente no podía hacer antes): ángulo "antes no podías X, ahora sí". Tono alto.
- "mejora" (Mejora de funcionalidad existente): ángulo "ya lo hacías, ahora mejor / más rápido / con menos fricción". Enmárcalo por tiempo ahorrado o errores evitados.
- "correccion" (Corrección de errores, o mantenimiento = true): sin épica NUNCA. Si la corrección toca la integridad de la factura o el dinero del cliente (cálculos, indexados, liquidaciones), conviértela en un mensaje sobrio de fiabilidad ("tu facturación, más a prueba de descuadres"). Si es trivial o de caso borde, NO le hagas item propio: agrúpalo en "mantenimiento_resumen".

ESTRUCTURA DE CADA ITEM: un "titulo" de beneficio de menos de 10 palabras + un "cuerpo" de 1 o 2 frases. Brevedad agresiva.

CONSOLIDACIÓN: si dos o más desarrollos tienen "relacionado_con" entre sí o son claramente lo mismo, fúndelos en un único item.

NO INVENTES. Si para contar bien el valor te falta un dato que no se deduce de las observaciones (la norma exacta, el beneficio concreto, a qué perfil de cliente aplica), NO te lo inventes: ponlo entre ⟨ ⟩ y añádelo a "necesita_confirmacion". Nunca inventes normas, artículos, fechas, cifras ni efectos legales.

RED DE SEGURIDAD: si un desarrollo es claramente trabajo interno y no una funcionalidad de producto (p. ej. "Apoyo a [persona]", "ayudar con la integración de X"), no lo conviertas en item: mételo en "excluidos" con el motivo. Plomería puramente técnica sin efecto visible para el cliente (adaptaciones de certificados, llamadas internas) también va a "excluidos" salvo que tenga un beneficio claro y nombrable.

SALIDA: devuelve EXCLUSIVAMENTE un objeto JSON válido con esta forma, sin markdown, sin texto antes ni después:
{
  "asunto": "...",
  "items": [{ "id": "...", "peso": "...", "titulo": "...", "cuerpo": "...", "modulo": "...", "aplica_a": "...", "necesita_confirmacion": [] }],
  "mantenimiento_resumen": "..." | null,
  "excluidos": [{ "id": "...", "titulo_crudo": "...", "motivo": "..." }]
}"""


def adaptar_correo(desarrollos: list) -> dict:
    """
    Llama a OpenAI con el system prompt del canal correo y devuelve el JSON parseado.
    `desarrollos` = lista de dicts con los campos en crudo marcados para correo.
    """
    from app.config import get_settings
    settings = get_settings()

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY no configurada")

    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai package no instalado")

    client = OpenAI(api_key=settings.openai_api_key)
    model = settings.comunicaciones_ai_model

    user_message = json.dumps({"desarrollos": desarrollos}, ensure_ascii=False, indent=2)

    # Responses API con forzado de JSON
    raw = None
    try:
        if hasattr(client, "responses"):
            resp = client.responses.create(
                model=model,
                instructions=SYSTEM_PROMPT_CORREO,
                input=user_message,
                temperature=0.4,
                max_output_tokens=4000,
                text={"format": {"type": "json_object"}},
            )
            raw = resp.output_text.strip()
        else:
            raise AttributeError("responses API no disponible")
    except Exception as e:
        logger.warning(f"[comunicaciones] Responses API fallo ({e}); fallback a Chat Completions")
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_CORREO},
                {"role": "user", "content": user_message},
            ],
            temperature=0.4,
            response_format={"type": "json_object"},
            max_completion_tokens=4000,
        )
        raw = resp.choices[0].message.content.strip()

    # Parsear JSON (tolerante a fences accidentales)
    cleaned = raw
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"[comunicaciones] respuesta IA no es JSON valido: {raw[:300]}")
        raise RuntimeError(f"La IA no devolvió JSON válido: {e}")

    # Normalizar claves esperadas
    data.setdefault("asunto", "Novedades BOMP")
    data.setdefault("items", [])
    data.setdefault("mantenimiento_resumen", None)
    data.setdefault("excluidos", [])
    return data


# ---------------------------------------------------------------------------
# Maquetación HTML email-safe (spec sección 6.2)
# ---------------------------------------------------------------------------

PESO_LABEL = {
    "regulatorio": "Regulatorio",
    "hito": "Novedad",
    "mejora": "Mejora",
    "correccion": "Fiabilidad",
}
PESO_COLOR = {
    "regulatorio": "#F59E0B",
    "hito": "#004975",
    "mejora": "#00B4D8",
    "correccion": "#64748B",
}
# Orden de aparición: regulatorio primero
PESO_ORDEN = {"regulatorio": 0, "hito": 1, "mejora": 2, "correccion": 3}


def _esc(s) -> str:
    return (
        str(s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_email_html(contenido: dict, firma: str = "El equipo de ASIC XXI", nombre: str = "{{nombre}}") -> str:
    """
    Construye el HTML email-safe a partir del JSON adaptado (contenido_editado o _generado).
    Mantiene {{nombre}} como placeholder por defecto para personalizar en el envío.
    """
    items = contenido.get("items", []) or []
    items_sorted = sorted(items, key=lambda it: PESO_ORDEN.get(it.get("peso", "mejora"), 9))
    mantenimiento = contenido.get("mantenimiento_resumen")

    bloques = []
    for it in items_sorted:
        peso = it.get("peso", "mejora")
        color = PESO_COLOR.get(peso, "#00B4D8")
        etiqueta = PESO_LABEL.get(peso, peso.capitalize())
        titulo = _esc(it.get("titulo", ""))
        cuerpo = _esc(it.get("cuerpo", ""))
        bloques.append(f"""
    <tr><td style="padding:14px 32px;">
      <span style="display:inline-block;background:{color};color:#fff;font-size:11px;font-weight:700;
            text-transform:uppercase;letter-spacing:.06em;padding:3px 10px;border-radius:20px;">{etiqueta}</span>
      <h2 style="margin:10px 0 6px;color:#003354;font-size:18px;font-weight:800;line-height:1.25;">{titulo}</h2>
      <p style="margin:0;color:#475569;font-size:14px;line-height:1.6;">{cuerpo}</p>
    </td></tr>""")

    mant_html = ""
    if mantenimiento:
        mant_html = f"""
    <tr><td style="padding:14px 32px;color:#64748B;font-size:13px;font-style:italic;">{_esc(mantenimiento)}</td></tr>"""

    firma_html = _esc(firma).replace("\n", "<br>")

    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F8FAFC;padding:24px 0;">
 <tr><td align="center">
  <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:12px;overflow:hidden;font-family:Inter,Arial,Helvetica,sans-serif;">
    <tr><td style="background:#004975;padding:24px 32px;">
      <span style="color:#FFFFFF;font-size:18px;font-weight:800;">ASIC<span style="color:#90E0EF;">XXI</span></span>
      <span style="color:rgba(255,255,255,.7);font-size:13px;float:right;">Novedades BOMP</span>
    </td></tr>
    <tr><td style="padding:28px 32px 8px;color:#0F172A;font-size:15px;">Hola {nombre},</td></tr>
    {''.join(bloques)}
    {mant_html}
    <tr><td style="padding:20px 32px 28px;color:#0F172A;font-size:14px;">Un saludo,<br>{firma_html}</td></tr>
    <tr><td style="background:#F1F5F9;padding:16px 32px;color:#94A3B8;font-size:12px;text-align:center;">
      ASIC XXI · Back-office y software para comercializadoras
    </td></tr>
  </table>
 </td></tr>
</table>"""
