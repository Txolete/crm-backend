from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.database import init_db
from app.api.routes import auth, admin, accounts, contacts, opportunities, tasks, activities, kanban, dashboard, import_excel, config, config_ui, admin_automations, ai
from datetime import datetime
import logging
import os

# Logging will be configured in startup_event (PASO 9)
logger = logging.getLogger(__name__)

# Load and validate settings (will fail if SECRET_KEY is not configured)
try:
    settings = get_settings()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="CRM para seguimiento comercial - MVP v0.1.0"
)

# CORS middleware - configured for local development
# Frontend and backend served from same host/port (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),  # Specific localhost origins from config
    allow_credentials=settings.cors_allow_credentials,  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(accounts.router)
app.include_router(contacts.router)
app.include_router(opportunities.router)
app.include_router(tasks.router)
app.include_router(activities.router)
app.include_router(kanban.router)
app.include_router(dashboard.router)
app.include_router(import_excel.router)
app.include_router(config.router)
app.include_router(config_ui.router)
app.include_router(admin_automations.router)
app.include_router(ai.router)


@app.on_event("startup")
async def startup_event():
    """Initialize application - PASO 9 enhanced"""
    # PASO 9 - Setup logging first
    from app.utils.logging_config import setup_logging
    setup_logging()
    
    startup_logger = logging.getLogger(__name__)
    
    # PASO 9 - Validate configuration
    from app.utils.config_validation import validate_config
    try:
        validate_config()
    except RuntimeError as e:
        startup_logger.critical(f"Startup failed: {e}")
        raise
    
    # Initialize database
    startup_logger.info("Initializing database...")
    init_db()
    startup_logger.info("Database initialized successfully")

    # Seed cfg_ai_prompts if table is empty (migration may have skipped INSERTs)
    from app.database import SessionLocal
    from app.models.config import CfgAiPrompt
    db_prompts = SessionLocal()
    try:
        prompt_count = db_prompts.query(CfgAiPrompt).count()
        if prompt_count == 0:
            startup_logger.warning("⚠️  cfg_ai_prompts vacío — insertando prompts por defecto...")
            from datetime import datetime, timezone as tz
            default_prompts = [
                CfgAiPrompt(
                    agent='client',
                    name='Agente Cliente',
                    system_prompt="""Eres el agente "Cliente" de un CRM B2B del sector energético en España.
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
                ),
                CfgAiPrompt(
                    agent='sales',
                    name='Agente Comercial',
                    system_prompt="""Eres el agente "Comercial" de un CRM B2B del sector energético en España.
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
                ),
                CfgAiPrompt(
                    agent='memory',
                    name='Agente Memoria',
                    system_prompt="""Eres el agente "Memoria Corporativa" de un CRM B2B del sector energético en España.
Tu función es detectar patrones en el historial de oportunidades cerradas y aplicarlos a la oportunidad actual.

Cuando recibas el contexto de una oportunidad y el histórico de casos similares:
1. Identifica patrones de éxito y fracaso en oportunidades similares (sector, valor, stage, tipo)
2. Compara el comportamiento actual con los casos ganados: ¿qué tienen en común?
3. Compara con los casos perdidos: ¿hay señales de alerta presentes aquí también?
4. Estima una probabilidad real basada en el histórico (no en la configurada en el CRM)
5. Si no hay suficientes datos históricos, indícalo claramente

Responde con datos concretos del histórico si los tienes, o con patrones generales del sector si no.
Responde siempre en español. Máximo 6-7 líneas."""
                ),
            ]
            for p in default_prompts:
                db_prompts.add(p)
            db_prompts.commit()
            startup_logger.info("✅ cfg_ai_prompts sembrado con 3 agentes por defecto")
        else:
            startup_logger.info(f"cfg_ai_prompts ya tiene {prompt_count} agente(s) — OK")
    except Exception as e:
        startup_logger.error(f"Error seeding cfg_ai_prompts: {e}")
        db_prompts.rollback()
    finally:
        db_prompts.close()

    # HOTFIX 9.4 - Initialize master data (cfg_* tables) if missing
    # In the original project this data was often present inside a pre-filled SQLite DB.
    # When starting from a clean database, we must create the default lists (stages,
    # regions, customer types, lead sources, contact roles, task templates).
    from app.database import SessionLocal
    from app.models.config import CfgStage
    from app.utils.init_master_data import initialize_all_master_data

    db_master = SessionLocal()
    try:
        stages_count = db_master.query(CfgStage).count()
        if stages_count == 0:
            startup_logger.warning(
                "⚠️  No master data found - initializing default lists (cfg_*)..."
            )
            initialize_all_master_data(db_master, startup_logger)
            startup_logger.info("✅ Master data initialized")
        else:
            startup_logger.info(
                f"Master data already present (cfg_stages={stages_count}) - skipping initialization"
            )
    except Exception as e:
        startup_logger.error(f"Error during master data initialization: {e}")
        db_master.rollback()
    finally:
        db_master.close()
    
    # HOTFIX 9.2 - Bootstrap admin if no users exist
    from app.models.user import User
    from app.utils.security import hash_password
    from app.utils.audit import generate_id, get_iso_timestamp, get_utc_now, create_audit_log, ENTITY_USERS
    
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            startup_logger.warning("⚠️  No users found in database - creating bootstrap admin...")
            timestamp = get_utc_now()
            admin_user = User(
                id=generate_id(),
                name=settings.admin_bootstrap_name,
                email=settings.admin_bootstrap_email,
                password_hash=hash_password(settings.admin_bootstrap_password),
                role="admin",
                is_active=1,
                last_login_at=None,
                created_at=timestamp,
                updated_at=timestamp
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            # Create audit log
            create_audit_log(
                db=db,
                entity=ENTITY_USERS,
                entity_id=admin_user.id,
                action="create",
                user_id=None,  # System action
                after_data={
                    "name": admin_user.name,
                    "email": admin_user.email,
                    "role": admin_user.role,
                    "is_active": True,
                    "created_by": "bootstrap"
                }
            )
            
            startup_logger.info("✅ Bootstrap admin created successfully!")
            startup_logger.info(f"   Email: {settings.admin_bootstrap_email}")
            startup_logger.info(f"   Password: {settings.admin_bootstrap_password}")
            startup_logger.warning("   ⚠️  CHANGE THIS PASSWORD AFTER FIRST LOGIN!")
        else:
            startup_logger.info(f"Found {user_count} existing user(s) - skipping bootstrap")
    except Exception as e:
        startup_logger.error(f"Error during bootstrap admin check: {e}")
        db.rollback()
    finally:
        db.close()
    
    startup_logger.info(f"CORS enabled for origins: {settings.get_cors_origins()}")
    startup_logger.info(f"Cookie configuration: name={settings.cookie_name}, secure={settings.cookie_secure}, samesite={settings.cookie_samesite}")
    
    # PASO 8 - Start automation scheduler
    from app.automations.scheduler import start_scheduler
    start_scheduler()
    startup_logger.info("Automation scheduler initialized")
    
    # PASO 9 - Add error handlers
    from app.middleware.error_handlers import add_error_handlers
    add_error_handlers(app)
    startup_logger.info("Error handlers registered")


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirect to dashboard"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/info")
async def app_info():
    """API information endpoint"""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "endpoints": {
            "auth": "/auth",
            "admin": "/admin",
            "accounts": "/accounts",
            "contacts": "/contacts",
            "opportunities": "/opportunities",
            "tasks": "/tasks",
            "activities": "/activities",
            "kanban": "/kanban",
            "dashboard": "/dashboard",
            "dashboard_summary": "/dashboard/summary",
            "targets": "/targets",
            "docs": "/docs"
        }
    }


@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    """Serve login page"""
    from fastapi.templating import Jinja2Templates
    from fastapi.responses import HTMLResponse
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse(
        "login.html",
        {"request": request},
        status_code=200
    )


@app.get("/test", include_in_schema=False)
async def test_diagnostic_page(request: Request):
    """Test/diagnostic page for debugging API calls"""
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse(
        "test_api.html",
        {"request": request},
        status_code=200
    )


@app.get("/diagnostico", include_in_schema=False)
async def diagnostico_page(request: Request):
    """Diagnostic page for opportunities"""
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse(
        "diagnostico_opp.html",
        {"request": request},
        status_code=200
    )


@app.get("/test-crear-opp", include_in_schema=False)
async def test_crear_opp_page(request: Request):
    """Test page for creating opportunities"""
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse(
        "test_crear_opp.html",
        {"request": request},
        status_code=200
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint - PASO 9
    
    Returns:
    - Overall status
    - Database connectivity
    - Scheduler status
    - Email configuration
    - Automations configuration
    """
    from app.database import SessionLocal
    from app.automations.scheduler import scheduler
    from app.config import get_settings
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.7.0",
        "checks": {}
    }
    
    settings = get_settings()
    
    # Check database
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["checks"]["database"] = {
            "status": "ok",
            "type": "sqlite" if "sqlite" in settings.database_url else "postgresql"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check scheduler
    try:
        if scheduler and scheduler.running:
            jobs = scheduler.get_jobs()
            next_run = jobs[0].next_run_time.isoformat() if jobs else None
            health_status["checks"]["scheduler"] = {
                "status": "running",
                "enabled": settings.automations_enabled,
                "next_run": next_run
            }
        elif settings.automations_enabled:
            health_status["checks"]["scheduler"] = {
                "status": "disabled",
                "enabled": False
            }
        else:
            health_status["checks"]["scheduler"] = {
                "status": "disabled_by_config",
                "enabled": False
            }
    except Exception as e:
        health_status["checks"]["scheduler"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check email
    health_status["checks"]["email"] = {
        "enabled": settings.email_enabled,
        "configured": bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)
    }
    
    # Automations config
    health_status["checks"]["automations"] = {
        "enabled": settings.automations_enabled,
        "run_time": settings.auto_run_time if settings.automations_enabled else None
    }
    
    return health_status


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
