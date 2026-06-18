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

TONO ("Starship"): vende el beneficio concreto a lo grande, con épica de verdad. Si de verdad protege legalmente al cliente o le quita un dolor real, dilo con ambición y sin pedir perdón. La épica se construye con la APUESTA (lo que está en juego: un corte invalidado, una sanción, dinero perdido, horas quemadas) y con el CONTRASTE (antes sufrías esto / ahora estás cubierto). La grandeza la lleva el beneficio dicho en grande y la tensión real del sector, NUNCA el adjetivo hueco. Usa verbos con fuerza (blindar, cubrir, proteger, eliminar, cerrar el flanco). Frases prohibidas y similares: "líderes", "soluciones integrales", "vanguardia", "tecnología punta", "compromiso con la excelencia", "potente herramienta", "robusto", "innovador". Tono directo, tuteo, frases cortas y con punch. Jerga del sector eléctrico SÍ (OMIE, REE, CNMC, CUPS, ATR, indexado, liquidación, desvíos, impagos): demuestra que somos de los suyos. Jerga técnica interna NO (PBI, refactor, endpoint, XML, certificado salvo que el cliente lo use directamente).

CLASIFICACIÓN Y PESO. Asigna a cada item un "peso" y trátalo según su peso:
- "regulatorio" (tipo = Adaptación regulatoria): es el de MÁS valor. Ángulo: "BOMP ya lo cumple, te cubre, alguien vigila el BOE por ti". Va arriba. Si hay norma, menciónala; si no la hay en el dato, marca ⟨norma — confirmar⟩.
- "hito" (Nueva funcionalidad que el cliente no podía hacer antes): ángulo "antes no podías X, ahora sí". Tono alto.
- "mejora" (Mejora de funcionalidad existente): ángulo "ya lo hacías, ahora mejor / más rápido / con menos fricción". Enmárcalo por tiempo ahorrado o errores evitados.
- "correccion" (Corrección de errores, o mantenimiento = true): sin épica NUNCA. Si la corrección toca la integridad de la factura o el dinero del cliente (cálculos, indexados, liquidaciones), conviértela en un mensaje sobrio de fiabilidad ("tu facturación, más a prueba de descuadres"). Si es trivial o de caso borde, NO le hagas item propio: agrúpalo en "mantenimiento_resumen".

HERO / INTRO: genera un campo "intro": 1-2 frases de apertura que enganchen al cliente y transmitan que ASIC XXI crea valor de forma continua para su operativa. No es un saludo ni un "os presentamos las novedades": es un gancho con tensión real del sector ("Mientras tú facturas, el BOE no para. Por eso BOMP tampoco.") o una promesa de tranquilidad operativa. Tono Starship, una idea con fuerza, sin corporativo hueco. Es lo primero que lee el cliente bajo la cabecera.

ESTRUCTURA DE CADA ITEM: un "titulo" de beneficio de menos de 10 palabras + un "cuerpo" de 1 o 2 frases. Brevedad agresiva, pero con empaque: el título debe poder leerse solo y vender el beneficio; el cuerpo aterriza el qué-ganas con concreción (tiempo ahorrado, riesgo evitado, dinero protegido).

CONSOLIDACIÓN: si dos o más desarrollos tienen "relacionado_con" entre sí o son claramente lo mismo, fúndelos en un único item.

NO INVENTES. Si para contar bien el valor te falta un dato que no se deduce de las observaciones (la norma exacta, el beneficio concreto, a qué perfil de cliente aplica), NO te lo inventes: ponlo entre ⟨ ⟩ y añádelo a "necesita_confirmacion". Nunca inventes normas, artículos, fechas, cifras ni efectos legales.

RED DE SEGURIDAD: si un desarrollo es claramente trabajo interno y no una funcionalidad de producto (p. ej. "Apoyo a [persona]", "ayudar con la integración de X"), no lo conviertas en item: mételo en "excluidos" con el motivo. Plomería puramente técnica sin efecto visible para el cliente (adaptaciones de certificados, llamadas internas) también va a "excluidos" salvo que tenga un beneficio claro y nombrable.

CALIBRACIÓN (estudia estos ejemplos antes de redactar):

Ejemplo "Carta de impago con info normativa obligatoria":
- BIEN ✅ titulo: "Tus cartas de impago, blindadas". cuerpo: "Un defecto formal puede invalidarte un corte o una reclamación de deuda. A partir de ahora cada carta sale conforme a ⟨norma — confirmar⟩ sin que nadie la revise a mano." → APUESTA clara (corte invalidado), contraste, jerga del sector, épica sin adjetivo hueco.
- MEH 😐 titulo: "Mejora en las cartas de impago". cuerpo: "Hemos añadido información normativa a las cartas." → correcto pero plano: ni apuesta ni contraste, no se siente el valor.
- MAL ❌ titulo: "Innovadora solución integral para impagos". cuerpo: "Nuestra potente herramienta lleva el cumplimiento a la vanguardia." → adjetivos huecos prohibidos, protagonista nosotros, cero concreción.

Ejemplo "Controles en facturación indexada horaria":
- BIEN ✅ titulo: "Tu facturación horaria, a prueba de descuadres". cuerpo: "Reforzamos los controles que cuadran consumos, precios y horas en cada factura indexada y afinamos el cálculo de la última hora." → sobrio y fiable (es corrección que toca el dinero), beneficio tangible.
- MAL ❌ titulo: "¡Revoluciona tu facturación indexada!". → épica falsa en una corrección: prohibido, suena a humo.

SALIDA: devuelve EXCLUSIVAMENTE un objeto JSON válido con esta forma, sin markdown, sin texto antes ni después:
{
  "asunto": "...",
  "intro": "1-2 frases de gancho (hero)",
  "items": [{ "id": "...", "peso": "...", "titulo": "...", "cuerpo": "...", "modulo": "...", "aplica_a": "...", "necesita_confirmacion": [] }],
  "mantenimiento_resumen": "..." | null,
  "excluidos": [{ "id": "...", "titulo_crudo": "...", "motivo": "..." }]
}"""


HERO_MODIFIERS = {
    1: "\n\nNIVEL DE HERO: BAJO. El 'intro' debe ser sobrio y breve (una frase), sin grandilocuencia. Prioriza claridad sobre épica.",
    2: "\n\nNIVEL DE HERO: MEDIO. El 'intro' engancha con una idea con fuerza, equilibrando ambición y sobriedad.",
    3: "\n\nNIVEL DE HERO: ALTO. El 'intro' debe ser muy potente y memorable, con tensión real del sector y ambición máxima (sin caer en adjetivos huecos). Es lo primero que ve el cliente: que impacte.",
}


def build_system_prompt(prompt_text: Optional[str] = None, hero_level: int = 2, calibracion_extra: Optional[str] = None) -> str:
    """Construye el system prompt final: base (override o default) + hero level + calibracion extra."""
    base = (prompt_text or "").strip() or SYSTEM_PROMPT_CORREO
    out = base + HERO_MODIFIERS.get(hero_level, HERO_MODIFIERS[2])
    if calibracion_extra and calibracion_extra.strip():
        out += "\n\nCALIBRACIÓN ADICIONAL (feedback real del revisor, respétalo):\n" + calibracion_extra.strip()
    return out


def adaptar_correo(desarrollos: list, system_prompt: Optional[str] = None) -> dict:
    """
    Llama a OpenAI con el system prompt del canal correo y devuelve el JSON parseado.
    `desarrollos` = lista de dicts con los campos en crudo marcados para correo.
    `system_prompt` = prompt final ya construido (si None, usa el por defecto).
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
    sys_prompt = system_prompt or SYSTEM_PROMPT_CORREO

    user_message = json.dumps({"desarrollos": desarrollos}, ensure_ascii=False, indent=2)

    # Responses API con forzado de JSON
    raw = None
    try:
        if hasattr(client, "responses"):
            resp = client.responses.create(
                model=model,
                instructions=sys_prompt,
                input=user_message,
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
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_message},
            ],
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
    data.setdefault("intro", "")
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


def build_email_html(
    contenido: dict,
    firma: str = "El equipo de ASIC XXI",
    saludo: str = "Hola",
    logo_url: str = "",
    cta_web: str = "www.asicxxi.com",
    cta_email: str = "",
    cta_tel: str = "",
) -> str:
    """
    Construye el HTML email-safe a partir del JSON adaptado (contenido_editado o _generado).
    Mantiene {{nombre}} como placeholder por defecto para personalizar en el envío.
    """
    items = contenido.get("items", []) or []
    items_sorted = sorted(items, key=lambda it: PESO_ORDEN.get(it.get("peso", "mejora"), 9))
    mantenimiento = contenido.get("mantenimiento_resumen")
    intro = contenido.get("intro", "")

    # Cabecera con fondo blanco para que luzca el logo oficial (azul)
    if logo_url:
        cabecera_inner = f"""
      <img src="{_esc(logo_url)}" alt="ASIC XXI" height="40" style="height:40px;display:inline-block;border:0;vertical-align:middle;">
      <span style="color:#64748B;font-size:13px;float:right;padding-top:12px;">Novedades BOMP</span>"""
    else:
        cabecera_inner = """
      <span style="color:#004975;font-size:22px;font-weight:800;">aSIc<span style="color:#7FA8C9;">xxi</span></span>
      <span style="color:#64748B;font-size:13px;float:right;padding-top:8px;">Novedades BOMP</span>"""

    # Hero
    hero_html = ""
    if intro:
        hero_html = f"""
    <tr><td style="background:#003354;padding:26px 32px;">
      <p style="margin:0;color:#FFFFFF;font-size:19px;font-weight:700;line-height:1.4;">{_esc(intro)}</p>
    </td></tr>"""

    bloques = []
    for it in items_sorted:
        peso = it.get("peso", "mejora")
        color = PESO_COLOR.get(peso, "#00B4D8")
        etiqueta = PESO_LABEL.get(peso, peso.capitalize())
        titulo = _esc(it.get("titulo", ""))
        cuerpo = _esc(it.get("cuerpo", ""))
        # Badge tipo "pill" redondeado en todos los clientes:
        # - VML roundrect SOLO lo ve Outlook (dentro de comentario condicional)
        # - el <span> con border-radius lo ven el resto de clientes (oculto en Outlook con mso-hide)
        badge_w = len(etiqueta) * 13 + 48  # ancho holgado para que el texto no se corte en Outlook
        badge = f"""<!--[if mso]>
      <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word"
        href="#" style="height:34px;v-text-anchor:middle;width:{badge_w}px;mso-padding-alt:0;" arcsize="50%" stroke="f" fillcolor="{color}">
        <w:anchorlock/>
        <center style="color:#ffffff;font-family:Arial,sans-serif;font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;">{etiqueta}</center>
      </v:roundrect>
      <![endif]-->
      <!--[if !mso]><!-->
      <span style="display:inline-block;background:{color};color:#fff;font-size:14px;font-weight:700;
            text-transform:uppercase;letter-spacing:.06em;padding:8px 20px;border-radius:24px;line-height:1;">{etiqueta}</span>
      <!--<![endif]-->"""
        bloques.append(f"""
    <tr><td style="padding:16px 32px;border-bottom:1px solid #EEF2F6;">
      {badge}
      <h2 style="margin:10px 0 6px;color:#003354;font-size:18px;font-weight:800;line-height:1.25;">{titulo}</h2>
      <p style="margin:0;color:#475569;font-size:14px;line-height:1.6;">{cuerpo}</p>
    </td></tr>""")

    mant_html = ""
    if mantenimiento:
        mant_html = f"""
    <tr><td style="padding:14px 32px;color:#64748B;font-size:13px;font-style:italic;">{_esc(mantenimiento)}</td></tr>"""

    firma_html = _esc(firma).replace("\n", "<br>")

    # CTA con datos de contacto
    contacto_bits = []
    if cta_email:
        contacto_bits.append(f'<a href="mailto:{_esc(cta_email)}" style="color:#FFFFFF;text-decoration:underline;">{_esc(cta_email)}</a>')
    if cta_tel:
        contacto_bits.append(_esc(cta_tel))
    if cta_web:
        web_url = cta_web if cta_web.startswith("http") else "https://" + cta_web
        contacto_bits.append(f'<a href="{_esc(web_url)}" style="color:#FFFFFF;text-decoration:underline;">{_esc(cta_web)}</a>')
    contacto_line = " &nbsp;·&nbsp; ".join(contacto_bits)
    cta_html = f"""
    <tr><td style="background:#004975;padding:22px 32px;text-align:center;">
      <p style="margin:0 0 6px;color:#FFFFFF;font-size:16px;font-weight:800;">¿Quieres ver cómo te afecta a ti?</p>
      <p style="margin:0 0 12px;color:#B9D4E6;font-size:13px;">Te lo contamos en 15 minutos, sin compromiso.</p>
      <p style="margin:0;color:#FFFFFF;font-size:13px;">{contacto_line}</p>
    </td></tr>"""

    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F8FAFC;padding:24px 0;">
 <tr><td align="center">
  <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:12px;overflow:hidden;font-family:Inter,Arial,Helvetica,sans-serif;">
    <tr><td style="background:#FFFFFF;padding:20px 32px;border-bottom:3px solid #004975;">{cabecera_inner}
    </td></tr>
    {hero_html}
    <tr><td style="padding:26px 32px 6px;color:#0F172A;font-size:15px;">{_esc(saludo)},</td></tr>
    {''.join(bloques)}
    {mant_html}
    <tr><td style="padding:20px 32px 26px;color:#0F172A;font-size:14px;">Un saludo,<br>{firma_html}</td></tr>
    {cta_html}
    <tr><td style="background:#F1F5F9;padding:16px 32px;color:#94A3B8;font-size:12px;text-align:center;">
      ASIC XXI · Servicios de ingeniería · Back-office y software para comercializadoras
    </td></tr>
  </table>
 </td></tr>
</table>"""
