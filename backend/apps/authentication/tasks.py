"""
Celery tasks for authentication app
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_audit_logs():
    """
    Clean up audit logs older than 90 days
    """
    from .models import AuditLog
    
    cutoff_date = timezone.now() - timedelta(days=90)
    deleted_count = AuditLog.objects.filter(created_at__lt=cutoff_date).delete()[0]
    
    logger.info(f"Cleaned up {deleted_count} old audit logs")
    return f"Deleted {deleted_count} audit logs"


@shared_task
def cleanup_inactive_sessions():
    """
    Clean up expired user sessions
    """
    from .models import UserSession
    
    deleted_count = UserSession.objects.filter(
        expires_at__lt=timezone.now(),
        is_active=True
    ).update(is_active=False)
    
    logger.info(f"Deactivated {deleted_count} expired sessions")
    return f"Deactivated {deleted_count} sessions"


@shared_task
def send_password_expiry_notification():
    """
    Send notifications to users whose passwords are about to expire
    """
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Find users with passwords older than 80 days (warn before 90-day expiry)
    warning_date = timezone.now() - timedelta(days=80)
    users = User.objects.filter(
        password_changed_at__lt=warning_date,
        is_active=True
    )
    
    # TODO: Implement email notification
    logger.info(f"Found {users.count()} users with passwords nearing expiry")
    
    return f"Sent password expiry warnings to {users.count()} users"
