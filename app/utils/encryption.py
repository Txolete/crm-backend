"""
Cifrado de datos personales en columna (ENS / RGPD).

Enfoque:
- EncryptedString: TypeDecorator de SQLAlchemy que cifra al guardar y descifra al leer,
  de forma transparente. Usa Fernet (AES-128-CBC + HMAC-SHA256, con IV aleatorio por valor).
- blind_index: HMAC-SHA256 del valor normalizado, para poder BUSCAR/DEDUPLICAR por
  coincidencia exacta sin exponer el dato en claro (ej. CIF, email).

Claves (variables de entorno, NUNCA en el repo):
- ENCRYPTION_KEY: clave Fernet (urlsafe base64, 32 bytes). Genera una con:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
- ENCRYPTION_INDEX_KEY: clave HMAC para los índices ciegos (cualquier cadena larga aleatoria).

Compatibilidad hacia atrás (migración gradual segura):
- Si un valor almacenado NO es un token Fernet válido (dato heredado en claro, aún sin
  migrar), process_result_value lo devuelve tal cual. Así la app sigue funcionando durante
  la migración de datos.
- Si no hay ENCRYPTION_KEY configurada (p. ej. dev local sin cifrado), el tipo pasa el valor
  en claro y avisa por log. En producción la clave DEBE estar configurada.
"""
import os
import hmac
import hashlib
import logging
from typing import Optional

from sqlalchemy import TypeDecorator, Text

logger = logging.getLogger(__name__)

_FERNET = None
_INDEX_KEY: Optional[bytes] = None
_WARNED_NO_KEY = False


def _get_fernet():
    global _FERNET
    if _FERNET is not None:
        return _FERNET
    key = os.getenv("ENCRYPTION_KEY", "").strip()
    if not key:
        return None
    from cryptography.fernet import Fernet
    _FERNET = Fernet(key.encode() if isinstance(key, str) else key)
    return _FERNET


def _get_index_key() -> Optional[bytes]:
    global _INDEX_KEY
    if _INDEX_KEY is not None:
        return _INDEX_KEY
    k = os.getenv("ENCRYPTION_INDEX_KEY", "").strip()
    if not k:
        # Fallback: derivar de ENCRYPTION_KEY si existe (mejor que nada, pero conviene una propia)
        k = os.getenv("ENCRYPTION_KEY", "").strip()
    if not k:
        return None
    _INDEX_KEY = k.encode()
    return _INDEX_KEY


def encrypt_value(plaintext: Optional[str]) -> Optional[str]:
    """Cifra un string. Devuelve token Fernet (str) o el valor en claro si no hay clave."""
    global _WARNED_NO_KEY
    if plaintext is None:
        return None
    if plaintext == "":
        return ""
    f = _get_fernet()
    if f is None:
        if not _WARNED_NO_KEY:
            logger.warning("[encryption] ENCRYPTION_KEY no configurada — datos se guardan EN CLARO")
            _WARNED_NO_KEY = True
        return plaintext
    return f.encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_value(stored: Optional[str]) -> Optional[str]:
    """Descifra un token Fernet. Si es dato heredado en claro (no token), lo devuelve tal cual."""
    if stored is None:
        return None
    if stored == "":
        return ""
    f = _get_fernet()
    if f is None:
        return stored
    from cryptography.fernet import InvalidToken
    try:
        return f.decrypt(stored.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        # Valor heredado en claro (aún no migrado) o clave rotada: devolver tal cual.
        return stored


def blind_index(value: Optional[str]) -> Optional[str]:
    """
    HMAC-SHA256 del valor normalizado (minúsculas, sin espacios extremos).
    Permite buscar/deduplicar por coincidencia exacta sin exponer el dato.
    """
    if value is None:
        return None
    norm = value.strip().lower()
    if norm == "":
        return None
    k = _get_index_key()
    if k is None:
        # Sin clave de índice: usar hash simple (menos seguro, pero funcional en dev)
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()
    return hmac.new(k, norm.encode("utf-8"), hashlib.sha256).hexdigest()


def is_encrypted(value: Optional[str]) -> bool:
    """True si el valor ya es un token Fernet válido (para migración idempotente)."""
    f = _get_fernet()
    if f is None or value is None or value == "":
        return False
    from cryptography.fernet import InvalidToken
    try:
        f.decrypt(value.encode("ascii"))
        return True
    except (InvalidToken, ValueError):
        return False


class EncryptedString(TypeDecorator):
    """
    Columna de texto cifrada de forma transparente.
    Se almacena como TEXT (el token Fernet es más largo que el original).
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return encrypt_value(value)

    def process_result_value(self, value, dialect):
        return decrypt_value(value)
