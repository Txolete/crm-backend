"""
Cifra los datos personales YA existentes en la BD (one-shot, idempotente).

Uso (con backup previo SIEMPRE):
    ENCRYPTION_KEY=... railway run --service crm-backend python scripts/encrypt_existing_pii.py --dry-run
    ENCRYPTION_KEY=... railway run --service crm-backend python scripts/encrypt_existing_pii.py --commit

Idempotente: un valor que ya es token Fernet válido se salta (no se re-cifra).
Trabaja con SQL directo sobre las columnas, sin pasar por el TypeDecorator, para poder
distinguir claro vs cifrado. Procesa por lotes.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.utils.encryption import encrypt_value, _get_fernet

# (tabla, columna) a cifrar en esta fase piloto. Se ampliará al resto de campos.
TARGETS = [
    ("contact_channels", "value"),
]

DRY = "--commit" not in sys.argv


def is_fernet_token(v: str) -> bool:
    f = _get_fernet()
    if f is None or v is None or v == "":
        return False
    from cryptography.fernet import InvalidToken
    try:
        f.decrypt(v.encode("ascii"))
        return True
    except (InvalidToken, ValueError):
        return False


def main():
    if _get_fernet() is None:
        print("ERROR: ENCRYPTION_KEY no configurada. Aborto.")
        sys.exit(1)

    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    eng = create_engine(db_url)

    total_enc = 0
    with eng.begin() as conn:
        for tabla, col in TARGETS:
            rows = conn.execute(text(f"SELECT id, {col} FROM {tabla}")).fetchall()
            n_enc = n_skip = 0
            for rid, val in rows:
                if val is None or val == "":
                    continue
                if is_fernet_token(val):
                    n_skip += 1
                    continue
                enc = encrypt_value(val)
                if not DRY:
                    conn.execute(
                        text(f"UPDATE {tabla} SET {col} = :v WHERE id = :id"),
                        {"v": enc, "id": rid},
                    )
                n_enc += 1
            total_enc += n_enc
            print(f"{tabla}.{col}: {n_enc} a cifrar, {n_skip} ya cifrados, {len(rows)} filas")

    print(f"\n{'[DRY-RUN] ' if DRY else '[COMMIT] '}Total a cifrar: {total_enc}")
    if DRY:
        print("Ejecuta con --commit para aplicar (haz backup antes).")


if __name__ == "__main__":
    main()
