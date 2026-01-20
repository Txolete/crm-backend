"""
Error Handling Middleware - PASO 9
Global exception handlers for consistent error responses
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


def add_error_handlers(app):
    """
    Add global error handlers to FastAPI app
    
    Handles:
    - HTTPException (400, 401, 403, 404, 409, etc)
    - RequestValidationError (422)
    - Generic Exception (500)
    """
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        Handle HTTP exceptions (400, 401, 403, 404, 409, etc)
        """
        # Determine if request expects JSON or HTML
        accept = request.headers.get("accept", "")
        is_api_request = (
            "application/json" in accept or
            request.url.path.startswith("/api/") or
            request.url.path.startswith("/auth/") or
            request.url.path.startswith("/admin/") or
            request.url.path.startswith("/accounts") or
            request.url.path.startswith("/opportunities") or
            request.url.path.startswith("/tasks") or
            request.url.path.startswith("/kanban") or
            request.url.path.startswith("/config-ui")
        )
        
        # Log error
        logger.warning(
            f"HTTP {exc.status_code}: {exc.detail} | "
            f"Path: {request.url.path} | "
            f"Method: {request.method}"
        )
        
        if is_api_request:
            # JSON response for API requests
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": True,
                    "status_code": exc.status_code,
                    "message": str(exc.detail),
                    "path": request.url.path
                }
            )
        else:
            # HTML response for browser requests
            return HTMLResponse(
                status_code=exc.status_code,
                content=get_error_html(exc.status_code, str(exc.detail))
            )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Handle validation errors (422)
        """
        logger.warning(
            f"Validation error: {exc.errors()} | "
            f"Path: {request.url.path} | "
            f"Method: {request.method}"
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": True,
                "status_code": 422,
                "message": "Validation error",
                "details": exc.errors(),
                "path": request.url.path
            }
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """
        Handle any unhandled exception (500)
        """
        # Log full error with traceback
        logger.error(
            f"Unhandled exception: {exc} | "
            f"Path: {request.url.path} | "
            f"Method: {request.method}",
            exc_info=True
        )
        
        # Determine if API request
        accept = request.headers.get("accept", "")
        is_api_request = "application/json" in accept or request.url.path.startswith("/api/")
        
        if is_api_request:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": True,
                    "status_code": 500,
                    "message": "Internal server error",
                    "path": request.url.path
                }
            )
        else:
            return HTMLResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=get_error_html(500, "Internal server error")
            )


def get_error_html(status_code: int, message: str) -> str:
    """
    Generate simple HTML error page
    """
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Validation Error",
        500: "Internal Server Error"
    }
    
    title = titles.get(status_code, "Error")
    
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{status_code} - {title}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                color: #333;
            }}
            .error-container {{
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                text-align: center;
                max-width: 500px;
            }}
            .error-code {{
                font-size: 72px;
                font-weight: 700;
                color: #667eea;
                margin: 0;
            }}
            .error-title {{
                font-size: 24px;
                margin: 10px 0;
                color: #333;
            }}
            .error-message {{
                color: #666;
                margin: 20px 0;
            }}
            .btn {{
                display: inline-block;
                padding: 12px 24px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin-top: 20px;
                transition: background 0.3s;
            }}
            .btn:hover {{
                background: #5568d3;
            }}
        </style>
    </head>
    <body>
        <div class="error-container">
            <div class="error-code">{status_code}</div>
            <h1 class="error-title">{title}</h1>
            <p class="error-message">{message}</p>
            <a href="/dashboard" class="btn">Volver al Dashboard</a>
        </div>
    </body>
    </html>
    """
