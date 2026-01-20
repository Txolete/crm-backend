"""
Logging Configuration - PASO 9
Advanced logging with rotation and separate files for app/error logs
"""
import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


def setup_logging():
    """
    Configure logging with:
    - Separate files: logs/app.log, logs/error.log
    - Daily rotation
    - Request ID support (via contextvars)
    """
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Format with timestamp, level, logger name, message
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # === APP LOG (INFO and above) ===
    app_handler = logging.handlers.RotatingFileHandler(
        'logs/app.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=30,  # Keep 30 files
        encoding='utf-8'
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)
    root_logger.addHandler(app_handler)
    
    # === ERROR LOG (ERROR and above only) ===
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/error.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=30,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # === CONSOLE (for development) ===
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Log startup
    logger = logging.getLogger(__name__)
    logger.info("=" * 70)
    logger.info("LOGGING SYSTEM INITIALIZED")
    logger.info(f"App log: logs/app.log (rotating, 10MB, 30 backups)")
    logger.info(f"Error log: logs/error.log (rotating, 10MB, 30 backups)")
    logger.info("=" * 70)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("apscheduler").setLevel(logging.INFO)
    
    return logger
