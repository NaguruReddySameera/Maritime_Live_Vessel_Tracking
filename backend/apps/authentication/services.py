"""
Authentication service layer for business logic
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import AuditLog, UserSession
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class AuthenticationService:
    """
    Service class for authentication-related business logic
    """
    
    @staticmethod
    def log_audit(user, action, resource_type, description, ip_address, user_agent, resource_id=None, request_data=None):
        """
        Create an audit log entry
        """
        try:
            AuditLog.objects.create(
                user=user,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                request_data=request_data or {}
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
    
    @staticmethod
    def create_user_session(user, token_jti, ip_address, user_agent, expires_at):
        """
        Create a new user session
        """
        try:
            session = UserSession.objects.create(
                user=user,
                token_jti=token_jti,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at
            )
            return session
        except Exception as e:
            logger.error(f"Failed to create user session: {str(e)}")
            return None
    
    @staticmethod
    def deactivate_user_sessions(user, token_jti=None):
        """
        Deactivate user sessions (all or specific)
        """
        try:
            query = UserSession.objects.filter(user=user, is_active=True)
            if token_jti:
                query = query.filter(token_jti=token_jti)
            query.update(is_active=False)
        except Exception as e:
            logger.error(f"Failed to deactivate sessions: {str(e)}")
    
    @staticmethod
    def get_active_sessions(user):
        """
        Get all active sessions for a user
        """
        return UserSession.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now()
        )
    
    @staticmethod
    def unlock_user_account(user):
        """
        Manually unlock a user account
        """
        user.failed_login_attempts = 0
        user.last_failed_login = None
        user.account_locked_until = None
        user.save(update_fields=['failed_login_attempts', 'last_failed_login', 'account_locked_until'])
        logger.info(f"User account unlocked: {user.email}")
    
    @staticmethod
    def reset_user_password(user, new_password):
        """
        Reset user password (admin function)
        """
        user.set_password(new_password)
        user.password_changed_at = timezone.now()
        user.save(update_fields=['password', 'password_changed_at'])
        logger.info(f"Password reset for user: {user.email}")
