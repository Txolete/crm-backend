from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./crm.db"
    
    # Security - SECRET_KEY is REQUIRED
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 días
    
    # Cookies configuration
    cookie_name: str = "crm_token"
    cookie_secure: bool = False  # False for local, True for production with HTTPS
    cookie_samesite: str = "lax"  # "lax" for local, "none" for cross-site with HTTPS
    cookie_max_age: int = 2592000  # 30 days in seconds
    
    # CORS configuration
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    cors_allow_credentials: bool = True
    
    # Bootstrap Admin (first-time setup)
    admin_bootstrap_email: str = "admin@example.com"
    admin_bootstrap_password: str = "admin123456"
    admin_bootstrap_name: str = "Admin User"
    
    # App
    app_name: str = "CRM Seguimiento Clientes"
    app_version: str = "0.5.0"
    
    # PASO 8 - Automations
    automations_enabled: bool = True
    auto_run_time: str = "07:00"  # HH:MM format
    auto_no_activity_days: int = 14
    auto_proposal_no_activity_days: int = 7
    auto_overdue_dedup_days: int = 7
    auto_followup_dedup_days: int = 14
    
    # PASO 8 - Email Notifications
    email_enabled: bool = True
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_tls: bool = True
    smtp_from_name: str = "CRM Notifications"
    smtp_from_email: str = ""
    email_dashboard_url: str = "http://localhost:8000/dashboard"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    def validate_secret_key(self):
        """
        Validate that SECRET_KEY is not the default insecure value
        This method should be called at startup
        """
        insecure_defaults = [
            "your-secret-key-here-change-in-production",
            "your-secret-key-must-be-changed-here",
            "change-this-secret-key",
            "insecure-secret-key"
        ]
        
        if not self.secret_key or self.secret_key in insecure_defaults:
            raise ValueError(
                "\n" + "="*70 + "\n"
                "CRITICAL SECURITY ERROR: SECRET_KEY is not configured!\n"
                "="*70 + "\n"
                "The SECRET_KEY must be set in your .env file with a secure random value.\n"
                "\n"
                "To generate a secure SECRET_KEY, run:\n"
                "  python -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
                "\n"
                "Then add it to your .env file:\n"
                "  SECRET_KEY=<generated-key-here>\n"
                "="*70
            )


@lru_cache()
def get_settings():
    settings = Settings()
    # Validate SECRET_KEY on startup
    settings.validate_secret_key()
    return settings
