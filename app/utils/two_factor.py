"""
2FA por email (OTP de 6 digitos). Obligatorio para admin; extensible a otros roles.
"""
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models.two_factor import TwoFactorCode
from app.models.user import User
from app.utils.security import hash_password, verify_password
from app.utils.audit import generate_id, get_utc_now

logger = logging.getLogger(__name__)

CODE_LENGTH = 6
CODE_TTL_MINUTES = 10
MAX_ATTEMPTS = 5

# Roles que requieren 2FA. Extensible: anadir "sales", "commercial" aqui cuando se decida.
ROLES_REQUIRING_2FA = {"admin"}


def role_requires_2fa(role: str) -> bool:
    return role in ROLES_REQUIRING_2FA


def generate_and_send_code(db: Session, user: User) -> str:
    """
    Genera un codigo de 6 digitos, lo guarda hasheado, invalida codigos previos sin usar,
    y lo envia por email. Devuelve el id del TwoFactorCode (challenge id) para el siguiente paso.
    """
    # Invalidar codigos anteriores no usados de este usuario
    db.query(TwoFactorCode).filter(
        TwoFactorCode.user_id == user.id,
        TwoFactorCode.used == 0,
    ).update({"used": 1})

    code = f"{secrets.randbelow(1_000_000):06d}"
    now = get_utc_now()
    tfc = TwoFactorCode(
        id=generate_id(),
        user_id=user.id,
        code_hash=hash_password(code),
        expires_at=now + timedelta(minutes=CODE_TTL_MINUTES),
        attempts=0,
        used=0,
        created_at=now,
    )
    db.add(tfc)
    db.commit()
    db.refresh(tfc)

    _send_code_email(user, code)
    return tfc.id


def verify_code(db: Session, challenge_id: str, code: str) -> Optional[User]:
    """
    Verifica el codigo contra el challenge. Devuelve el User si es valido, None si no.
    Incrementa intentos; bloquea tras MAX_ATTEMPTS.
    """
    tfc = db.query(TwoFactorCode).filter(TwoFactorCode.id == challenge_id).first()
    if not tfc or tfc.used == 1:
        return None

    now = get_utc_now()
    if tfc.expires_at.tzinfo is None:
        expires = tfc.expires_at.replace(tzinfo=timezone.utc)
    else:
        expires = tfc.expires_at
    if now > expires:
        return None

    if tfc.attempts >= MAX_ATTEMPTS:
        return None

    tfc.attempts += 1
    if not verify_password(code, tfc.code_hash):
        db.commit()
        return None

    tfc.used = 1
    db.commit()

    return db.query(User).filter(User.id == tfc.user_id).first()


def _send_code_email(user: User, code: str) -> None:
    from app.automations.email_service import send_email
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
        <h2 style="color:#004975;">Código de verificación — CRM ASIC XXI</h2>
        <p>Hola {user.name},</p>
        <p>Tu código de acceso es:</p>
        <p style="font-size: 32px; font-weight: 700; letter-spacing: 6px; color:#004975; margin: 20px 0;">{code}</p>
        <p style="color:#64748B; font-size: 13px;">Caduca en {CODE_TTL_MINUTES} minutos. Si no has intentado iniciar sesión, ignora este correo.</p>
    </div>
    """
    ok = send_email(user.email, "Tu código de verificación — CRM ASIC XXI", html)
    if not ok:
        logger.error(f"[2FA] No se pudo enviar el código a {user.email} — revisar configuración SMTP")
