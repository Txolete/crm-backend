"""
Admin endpoints for user management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse, UserResetPassword
)
from app.utils.security import hash_password
from app.utils.auth import require_role, get_current_user_from_cookie
from app.utils.audit import create_audit_log, generate_id, get_iso_timestamp, get_utc_now, ENTITY_USERS
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin - User Management"])

# Configure Jinja2 templates
templates = Jinja2Templates(directory="app/templates")


@router.get("/users-page", response_class=HTMLResponse)
async def users_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Serve users management page
    
    **Permissions:** Admin only
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access user management"
        )
    
    return templates.TemplateResponse(
        "users.html",
        {"request": request}
    )


@router.get("/users", response_model=UserListResponse)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "sales", "commercial"))
):
    """
    List all users

    **Admin and Sales** see all users (needed for owner assignment).
    **Commercial** only sees themselves (for owner dropdown in forms).

    Returns all users with their information (except password_hash)
    """
    if current_user.role == "commercial":
        users = db.query(User).filter(User.id == current_user.id).all()
    else:
        users = db.query(User).all()
    
    return UserListResponse(
        users=[
            UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role,
                is_active=user.is_active == 1,  # Convert INTEGER to bool
                last_login_at=user.last_login_at,
                created_at=user.created_at,
                updated_at=user.updated_at,
                email_signature=user.email_signature,
            )
            for user in users
        ],
        total=len(users)
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Create a new user
    
    **Admin only**
    
    - Checks if email already exists
    - Hashes the password
    - Creates user with initial password
    - Logs action in audit_log
    """
    # Check if email already exists (case-insensitive)
    normalized_email = user_data.email.strip().lower()
    existing_user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    timestamp = get_utc_now()
    new_user = User(
        id=generate_id(),
        name=user_data.name,
        email=normalized_email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        is_active=1,  # Active by default
        last_login_at=None,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    db.add(new_user)
    
    # Create audit log
    create_audit_log(
        db=db,
        entity=ENTITY_USERS,
        entity_id=new_user.id,
        action="create",
        user_id=current_user.id,
        after_data={
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role,
            "is_active": True
        }
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"User created by {current_user.email}: {new_user.email} ({new_user.role})")
    
    return UserResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,
        role=new_user.role,
        is_active=True,
        last_login_at=new_user.last_login_at,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
        email_signature=new_user.email_signature,
    )


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Update user information
    
    **Admin only**
    
    Can update:
    - name
    - email
    - role
    - is_active (activate/deactivate)
    
    Uses logical deletion (is_active) - never deletes users
    """
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Store before state
    before_data = {
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active == 1
    }
    
    # Update fields if provided
    if user_data.name is not None:
        user.name = user_data.name
    
    if user_data.email is not None:
        normalized_email = user_data.email.strip().lower()
        # Check if new email already exists (excluding current user, case-insensitive)
        existing = db.query(User).filter(
            func.lower(User.email) == normalized_email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        user.email = normalized_email
    
    if user_data.role is not None:
        user.role = user_data.role
    
    if user_data.is_active is not None:
        user.is_active = 1 if user_data.is_active else 0

    if user_data.email_signature is not None:
        user.email_signature = user_data.email_signature.strip() or None

    user.updated_at = get_utc_now()
    
    # Store after state
    after_data = {
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active == 1
    }
    
    # Determine action for audit log
    action = "update"
    if before_data["is_active"] != after_data["is_active"]:
        action = "activate" if after_data["is_active"] else "deactivate"
    
    # Create audit log
    create_audit_log(
        db=db,
        entity=ENTITY_USERS,
        entity_id=user.id,
        action=action,
        user_id=current_user.id,
        before_data=before_data,
        after_data=after_data
    )
    
    # Single commit at the end
    db.commit()
    db.refresh(user)
    
    logger.info(f"User updated by {current_user.email}: {user.email}")
    
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active == 1,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
        email_signature=user.email_signature,
    )


@router.post("/users/{user_id}/reset-password", response_model=dict)
def reset_user_password(
    user_id: str,
    password_data: UserResetPassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    Reset user password
    
    **Admin only**
    
    Sets a new password for the user
    """
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.password_hash = hash_password(password_data.new_password)
    user.updated_at = get_utc_now()
    
    # Create audit log
    create_audit_log(
        db=db,
        entity=ENTITY_USERS,
        entity_id=user.id,
        action="reset_password",
        user_id=current_user.id,
        after_data={
            "email": user.email,
            "password_reset_by": current_user.email
        }
    )
    
    # Single commit at the end
    db.commit()
    
    logger.info(f"Password reset by {current_user.email} for user: {user.email}")
    
    return {
        "message": "Password reset successfully",
        "user_id": user.id,
        "email": user.email
    }


# ===========================================================================
# Seguridad — cifrado de PII existente (ENS). Endpoint de un solo uso, idempotente.
# Se ejecuta DENTRO de Railway (donde la BD interna es alcanzable). Solo admin.
# ===========================================================================

_PII_TARGETS = [
    ("contact_channels", "value"),
    ("contacts", "first_name"),
    ("contacts", "last_name"),
    ("accounts", "email"),
    ("accounts", "phone"),
    ("accounts", "address"),
    ("accounts", "tax_id"),
    ("users", "email_signature"),
]


@router.post("/security/encrypt-existing-pii")
def encrypt_existing_pii(
    commit: bool = Query(False, description="false = dry-run (solo cuenta); true = aplica"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Cifra los datos personales ya existentes que aún estén en claro.
    Idempotente: los valores ya cifrados se saltan. Dry-run por defecto.
    """
    from app.utils.encryption import encrypt_value, is_encrypted, _get_fernet
    if _get_fernet() is None:
        raise HTTPException(status_code=400, detail="ENCRYPTION_KEY no configurada en el entorno")

    report = []
    total_enc = 0
    conn = db.connection()
    for tabla, col in _PII_TARGETS:
        rows = conn.execute(text(f"SELECT id, {col} FROM {tabla}")).fetchall()
        n_enc = n_skip = 0
        for rid, val in rows:
            if val is None or val == "":
                continue
            if is_encrypted(val):
                n_skip += 1
                continue
            if commit:
                conn.execute(
                    text(f"UPDATE {tabla} SET {col} = :v WHERE id = :id"),
                    {"v": encrypt_value(val), "id": rid},
                )
            n_enc += 1
        report.append({"tabla": tabla, "columna": col, "a_cifrar": n_enc, "ya_cifrados": n_skip, "filas": len(rows)})
        total_enc += n_enc
    if commit:
        db.commit()
    logger.info(f"[security] encrypt-existing-pii commit={commit} total_a_cifrar={total_enc}")
    return {"dry_run": not commit, "total_a_cifrar": total_enc, "detalle": report}


@router.get("/system/db-schema")
def db_schema(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Diagnostico de solo lectura: tablas/columnas reales en la BD + revision de
    alembic_version. Para investigar desfases entre el historial de migraciones
    y el esquema real (create_all crea tablas nuevas en cada deploy, lo que puede
    disimular que alembic no ha llegado a aplicar algunas migraciones).
    """
    conn = db.connection()
    rows = conn.execute(text(
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema='public' ORDER BY table_name, ordinal_position"
    )).fetchall()
    schema = {}
    for t, c in rows:
        schema.setdefault(t, []).append(c)
    try:
        version_rows = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        version = [v[0] for v in version_rows]
    except Exception as e:
        version = f"error: {e}"
    return {"alembic_version": version, "tables": schema}


@router.post("/system/run-migrations")
def run_migrations(
    current_user: User = Depends(require_role("admin")),
):
    """
    Ejecuta `alembic upgrade head` desde DENTRO del contenedor. Util cuando el
    pre-deploy configurado en Railway no ha llegado a aplicar las migraciones
    (síntoma: errores "column ... does not exist" tras un deploy) — desde la
    máquina local no se puede correr alembic directamente porque el host de
    Postgres interno de Railway no resuelve fuera de su red.
    """
    from alembic.config import Config
    from alembic import command
    import io
    import contextlib

    cfg = Config("alembic.ini")
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            command.upgrade(cfg, "head")
    except Exception as e:
        logger.error(f"[admin] run-migrations fallo: {e}\n{buf.getvalue()}")
        raise HTTPException(status_code=500, detail=f"Fallo al migrar: {e}")
    logger.info(f"[admin] migraciones aplicadas por {current_user.email}")
    return {"message": "Migraciones aplicadas hasta head", "output": buf.getvalue()}


@router.post("/security/test-smtp")
def test_smtp(
    current_user: User = Depends(require_role("admin")),
):
    """
    Envia un email de prueba a si mismo para validar que SMTP_USER/SMTP_PASSWORD
    estan correctamente configurados (usados tambien para el 2FA por email).
    """
    from app.automations.email_service import send_email
    ok = send_email(
        current_user.email,
        "Prueba SMTP — CRM ASIC XXI",
        "<p>Si ves este email, la configuración SMTP funciona correctamente.</p>",
    )
    if not ok:
        raise HTTPException(status_code=502, detail="No se pudo enviar. Revisa SMTP_USER/SMTP_PASSWORD/EMAIL_ENABLED en las variables de entorno.")
    return {"message": f"Email de prueba enviado a {current_user.email}"}
