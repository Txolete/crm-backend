"""
Scheduler - PASO 8
APScheduler for daily automations
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

from app.config import get_settings
from app.automations.jobs import run_all_automations
from app.automations.email_service import send_daily_task_emails

logger = logging.getLogger(__name__)

settings = get_settings()

# Global scheduler instance
scheduler = None


def daily_job():
    """
    Daily job that runs automations + emails
    
    Sequence:
    1. Run all 3 automations (overdue, no_activity, proposal_followup)
    2. Send daily task emails to users
    """
    logger.info("=" * 70)
    logger.info(f"DAILY JOB STARTED AT {datetime.now().isoformat()}")
    logger.info("=" * 70)
    
    try:
        # 1. Run automations
        automation_results = run_all_automations()
        logger.info(f"Automation results: {automation_results}")
        
        # 2. Send emails
        email_results = send_daily_task_emails()
        logger.info(f"Email results: {email_results}")
        
        logger.info("=" * 70)
        logger.info("DAILY JOB COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"DAILY JOB FAILED: {e}", exc_info=True)


def start_scheduler():
    """
    Start APScheduler if automations enabled
    
    Schedule daily job at AUTO_RUN_TIME (e.g. 07:00)
    """
    global scheduler
    
    if not settings.automations_enabled:
        logger.info("Automations disabled (AUTOMATIONS_ENABLED=false), scheduler not started")
        return None
    
    # Parse run time (HH:MM format)
    try:
        hour, minute = map(int, settings.auto_run_time.split(':'))
    except:
        logger.warning(f"Invalid AUTO_RUN_TIME format: {settings.auto_run_time}, using default 07:00")
        hour, minute = 7, 0
    
    # Create scheduler
    scheduler = BackgroundScheduler()
    
    # Add daily job
    trigger = CronTrigger(hour=hour, minute=minute)
    scheduler.add_job(
        daily_job,
        trigger=trigger,
        id='daily_automations',
        name='Daily Automations + Emails',
        replace_existing=True
    )
    
    # Start scheduler
    scheduler.start()
    
    logger.info("=" * 70)
    logger.info(f"SCHEDULER STARTED")
    logger.info(f"Daily job scheduled at {hour:02d}:{minute:02d}")
    logger.info(f"Next run: {scheduler.get_jobs()[0].next_run_time}")
    logger.info("=" * 70)
    
    return scheduler


def stop_scheduler():
    """Stop scheduler gracefully"""
    global scheduler
    
    if scheduler:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
