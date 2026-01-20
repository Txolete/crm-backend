"""
Configuration Validation - PASO 9
Validate config at startup and auto-fix when possible
"""
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)


def validate_config():
    """
    Validate configuration at startup
    
    Checks:
    - SECRET_KEY is secure
    - Email settings (warn if incomplete, auto-disable)
    - Automation settings
    - Database path
    
    Returns: validated settings object
    """
    settings = get_settings()
    warnings = []
    errors = []
    
    logger.info("=" * 70)
    logger.info("CONFIGURATION VALIDATION")
    logger.info("=" * 70)
    
    # === SECRET_KEY ===
    try:
        settings.validate_secret_key()
        logger.info("✓ SECRET_KEY: OK")
    except ValueError as e:
        errors.append(str(e))
        logger.error(f"✗ SECRET_KEY: {e}")
    
    # === EMAIL SETTINGS ===
    if settings.email_enabled:
        email_ok = True
        missing_fields = []
        
        if not settings.smtp_host:
            missing_fields.append("SMTP_HOST")
            email_ok = False
        if not settings.smtp_user:
            missing_fields.append("SMTP_USER")
            email_ok = False
        if not settings.smtp_password:
            missing_fields.append("SMTP_PASSWORD")
            email_ok = False
        
        if not email_ok:
            # Auto-disable email
            settings.email_enabled = False
            warning_msg = (
                f"Email enabled but missing required fields: {', '.join(missing_fields)}. "
                "Email notifications automatically disabled."
            )
            warnings.append(warning_msg)
            logger.warning(f"⚠ EMAIL: {warning_msg}")
        else:
            logger.info(f"✓ EMAIL: Enabled ({settings.smtp_host}:{settings.smtp_port})")
    else:
        logger.info("✓ EMAIL: Disabled")
    
    # === AUTOMATIONS ===
    if settings.automations_enabled:
        # Validate AUTO_RUN_TIME format
        try:
            hour, minute = map(int, settings.auto_run_time.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid time")
            logger.info(f"✓ AUTOMATIONS: Enabled (run at {settings.auto_run_time})")
        except:
            warning_msg = f"Invalid AUTO_RUN_TIME format: {settings.auto_run_time}. Using default 07:00"
            warnings.append(warning_msg)
            logger.warning(f"⚠ AUTOMATIONS: {warning_msg}")
            settings.auto_run_time = "07:00"
        
        # Log thresholds
        logger.info(f"  - No activity threshold: {settings.auto_no_activity_days} days")
        logger.info(f"  - Proposal threshold: {settings.auto_proposal_no_activity_days} days")
        logger.info(f"  - Overdue dedupe: {settings.auto_overdue_dedup_days} days")
        logger.info(f"  - Follow-up dedupe: {settings.auto_followup_dedup_days} days")
    else:
        logger.info("✓ AUTOMATIONS: Disabled")
    
    # === DATABASE ===
    logger.info(f"✓ DATABASE: {settings.database_url}")
    
    # === CORS ===
    origins = settings.get_cors_origins()
    logger.info(f"✓ CORS: {len(origins)} origins configured")
    
    # === Summary ===
    logger.info("=" * 70)
    if errors:
        logger.error(f"VALIDATION FAILED: {len(errors)} error(s)")
        for error in errors:
            logger.error(f"  - {error}")
        raise RuntimeError("Configuration validation failed. Check logs.")
    
    if warnings:
        logger.warning(f"VALIDATION COMPLETED WITH WARNINGS: {len(warnings)}")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    else:
        logger.info("CONFIGURATION VALIDATION PASSED")
    
    logger.info("=" * 70)
    
    return settings
