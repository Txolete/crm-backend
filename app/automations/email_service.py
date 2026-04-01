"""
Email Notifications Service - PASO 8
Send daily task summary emails to users
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.opportunity import Task, Opportunity
from app.models.account import Account
from app.models.user import User
from app.models.config import CfgStage
from app.utils.audit import create_audit_log, generate_id, get_iso_timestamp
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

settings = get_settings()


def get_user_tasks_summary(user_id: str, db: Session) -> Dict:
    """
    Get task summary for a user
    
    Returns dict with:
    - overdue: tasks with due_date < today
    - due_soon: tasks with due_date in next 2 days
    - upcoming: tasks with due_date in next 3-10 days
    """
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    ten_days = today + timedelta(days=10)
    
    # Query tasks assigned to user
    base_query = db.query(Task, Opportunity, Account, CfgStage).join(
        Opportunity, Task.opportunity_id == Opportunity.id
    ).join(
        Account, Opportunity.account_id == Account.id
    ).join(
        CfgStage, Opportunity.stage_id == CfgStage.id
    ).filter(
        Task.assigned_to_user_id == user_id,
        Task.status == 'open',
        Task.due_date.isnot(None)
    )
    
    # Overdue
    overdue = base_query.filter(
        Task.due_date < today
    ).all()

    # Due soon (today + next 2 days)
    due_soon = base_query.filter(
        Task.due_date >= today,
        Task.due_date <= day_after
    ).all()

    # Upcoming (next 3-10 days)
    upcoming = base_query.filter(
        Task.due_date > day_after,
        Task.due_date <= ten_days
    ).all()
    
    return {
        'overdue': overdue,
        'due_soon': due_soon,
        'upcoming': upcoming
    }


def generate_email_html(user: User, tasks_summary: Dict, dashboard_url: str) -> str:
    """Generate HTML email body"""
    
    overdue = tasks_summary['overdue']
    due_soon = tasks_summary['due_soon']
    upcoming = tasks_summary['upcoming']
    
    # Helper function to format task list
    def format_task_list(tasks, color):
        if not tasks:
            return f'<p style="color: #666;">Sin tareas</p>'
        
        html = '<ul style="list-style: none; padding: 0;">'
        for task, opp, account, stage in tasks:
            html += f'''
            <li style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-left: 4px solid {color};">
                <strong>{task.title}</strong><br>
                <span style="color: #666; font-size: 0.9em;">
                    📅 Vence: {task.due_date} | 
                    🏢 {account.name} | 
                    📊 {stage.name}
                </span>
            </li>
            '''
        html += '</ul>'
        return html
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #0066cc; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: white; padding: 20px; border: 1px solid #dee2e6; }}
            .section {{ margin-bottom: 30px; }}
            .section-title {{ font-size: 1.2em; font-weight: 600; margin-bottom: 10px; border-bottom: 2px solid #dee2e6; padding-bottom: 5px; }}
            .button {{ display: inline-block; padding: 12px 24px; background: #0066cc; color: white; text-decoration: none; border-radius: 4px; margin-top: 20px; }}
            .footer {{ text-align: center; color: #666; font-size: 0.9em; padding: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📋 Resumen Diario de Tareas</h1>
                <p>Hola {user.name},</p>
            </div>
            
            <div class="content">
                <p>Este es tu resumen de tareas para hoy, {datetime.now().strftime('%d/%m/%Y')}:</p>
                
                <div class="section">
                    <div class="section-title">
                        🔴 VENCIDAS ({len(overdue)})
                    </div>
                    {format_task_list(overdue, '#dc3545')}
                </div>
                
                <div class="section">
                    <div class="section-title">
                        🟡 PRÓXIMOS 2 DÍAS ({len(due_soon)})
                    </div>
                    {format_task_list(due_soon, '#ffc107')}
                </div>
                
                <div class="section">
                    <div class="section-title">
                        🟢 PRÓXIMOS 10 DÍAS ({len(upcoming)})
                    </div>
                    {format_task_list(upcoming, '#28a745')}
                </div>
                
                <div style="text-align: center;">
                    <a href="{dashboard_url}" class="button">Ir al Dashboard</a>
                </div>
            </div>
            
            <div class="footer">
                <p>Este es un email automático del CRM.</p>
                <p>Por favor no respondas a este mensaje.</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send email via SMTP"""
    if not settings.email_enabled:
        logger.info(f"Email disabled, skipping send to {to_email}")
        return False
    
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP credentials not configured, skipping email")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{settings.smtp_from_name} <{settings.smtp_from_email or settings.smtp_user}>"
        msg['To'] = to_email
        
        # Attach HTML
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Send via SMTP
        if settings.smtp_tls:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
        
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_daily_task_emails():
    """
    Send daily task summary email to all active users with tasks
    
    Called after automations run.
    Creates audit log for each email sent.
    """
    if not settings.email_enabled:
        logger.info("[EMAIL] Emails disabled, skipping")
        return {"sent": 0, "failed": 0, "skipped": 0}
    
    db = SessionLocal()
    
    try:
        # Get all active users
        users = db.query(User).filter(User.is_active == True).all()
        
        sent = 0
        failed = 0
        skipped = 0
        
        for user in users:
            # Get task summary
            tasks_summary = get_user_tasks_summary(user.id, db)
            
            # Check if user has any tasks
            total_tasks = (
                len(tasks_summary['overdue']) + 
                len(tasks_summary['due_soon']) + 
                len(tasks_summary['upcoming'])
            )
            
            if total_tasks == 0:
                logger.info(f"[EMAIL] User {user.email} has no tasks, skipping")
                skipped += 1
                continue
            
            # Generate email
            html = generate_email_html(user, tasks_summary, settings.email_dashboard_url)
            subject = f"CRM: Resumen Diario - {len(tasks_summary['overdue'])} vencidas, {len(tasks_summary['due_soon'])} próximas"
            
            # Send email
            success = send_email(user.email, subject, html)
            
            if success:
                sent += 1
                
                # Audit log
                create_audit_log(
                    db=db,
                    entity="system",
                    entity_id=user.id,
                    action="daily_task_email",
                    user_id=None,  # System
                    after_data={
                        "user_id": user.id,
                        "user_email": user.email,
                        "overdue_count": len(tasks_summary['overdue']),
                        "due_soon_count": len(tasks_summary['due_soon']),
                        "upcoming_count": len(tasks_summary['upcoming'])
                    }
                )
            else:
                failed += 1
        
        db.commit()
        
        logger.info(f"[EMAIL] Daily emails: {sent} sent, {failed} failed, {skipped} skipped")
        return {"sent": sent, "failed": failed, "skipped": skipped}
        
    except Exception as e:
        db.rollback()
        logger.error(f"[EMAIL] Error sending daily emails: {e}")
        return {"sent": 0, "failed": 0, "skipped": 0, "error": str(e)}
    finally:
        db.close()
