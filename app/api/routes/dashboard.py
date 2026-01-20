"""
Dashboard endpoints
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.models.user import User
from app.utils.auth import get_current_user_from_cookie
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Configure Jinja2 templates
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Serve dashboard HTML page
    
    **Authentication:** Checked client-side via /auth/me
    If not authenticated, dashboard.js will redirect to /login
    
    **Permissions:** All authenticated users
    """
    settings = get_settings()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "app_meta": {
                "name": settings.app_name,
                "version": settings.app_version,
                # Release info for the UI "Acerca de" panel
                "release": "v1.0",
                "release_date": "2026-01-16",
                "features": [
                    "Dashboard con KPIs (pipeline total/ponderado, pacing)",
                    "Kanban de oportunidades con drag & drop",
                    "Gestión de clientes y contactos",
                    "Importación desde Excel",
		    "Dashboard de tareas",
                    "Catálogos (stages, regiones, tipos, fuentes) auto-cargados"
                ]
            }
        }
    )


@router.get("/config", response_class=HTMLResponse)
async def config_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Serve config management page
    
    **Permissions:** Admin only (enforced by API and frontend)
    """
    return templates.TemplateResponse(
        "config.html",
        {
            "request": request,
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
                "role": current_user.role
            }
        }
    )


@router.get("/test-won-lost", response_class=HTMLResponse)
async def test_won_lost(request: Request):
    """
    Test page to diagnose won/lost kanban issues
    """
    return templates.TemplateResponse(
        "test_kanban_won_lost.html",
        {"request": request}
    )


@router.get("/test-version", response_class=HTMLResponse)
async def test_version(request: Request):
    """
    Test page to verify dashboard.js version
    """
    return templates.TemplateResponse(
        "test_version.html",
        {"request": request}
    )
