"""
Custom User model with role-based access control
Implements: Operator, Analyst, Admin roles
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


class UserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Custom User model with three-tier role system:
    - Operator: View vessels, add notes, basic access
    - Analyst: All Operator permissions + analytics, reports, historical data
    - Admin: Full system access including user management and configurations
    """
    
    ROLE_CHOICES = [
        ('operator', 'Operator'),
        ('analyst', 'Analyst'),
        ('admin', 'Admin'),
    ]
    
    # Core Fields
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='operator', db_index=True)
    
    # Authentication Fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # Security Fields
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(default=timezone.now)
    
    # Profile Fields
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    organization = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Activity Tracking
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_activity = models.DateTimeField(default=timezone.now)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['role', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    def get_full_name(self):
        """Return user's full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def is_account_locked(self):
        """Check if account is locked due to failed login attempts"""
        if self.account_locked_until and self.account_locked_until > timezone.now():
            return True
        return False
    
    def record_failed_login(self):
        """Record a failed login attempt"""
        from django.conf import settings
        from datetime import timedelta
        
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        
        # Lock account if threshold exceeded
        if self.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            self.account_locked_until = timezone.now() + timedelta(
                minutes=settings.ACCOUNT_LOCKOUT_MINUTES
            )
        
        self.save(update_fields=['failed_login_attempts', 'last_failed_login', 'account_locked_until'])
    
    def reset_failed_logins(self):
        """Reset failed login attempts after successful login"""
        if self.failed_login_attempts > 0:
            self.failed_login_attempts = 0
            self.last_failed_login = None
            self.account_locked_until = None
            self.save(update_fields=['failed_login_attempts', 'last_failed_login', 'account_locked_until'])
    
    def has_permission(self, permission):
        """Check if user has specific permission based on role"""
        permissions = {
            'operator': [
                'view_vessels',
                'add_vessel_notes',
                'view_ports',
                'view_own_dashboard',
            ],
            'analyst': [
                'view_vessels',
                'add_vessel_notes',
                'view_ports',
                'view_analytics',
                'view_historical_data',
                'create_reports',
                'view_safety_data',
                'create_dashboard',
                'view_own_dashboard',
                'view_voyage_replay',
            ],
            'admin': [
                'view_vessels',
                'add_vessel_notes',
                'manage_vessels',
                'view_ports',
                'manage_ports',
                'view_analytics',
                'view_historical_data',
                'create_reports',
                'view_safety_data',
                'manage_safety_data',
                'create_dashboard',
                'view_all_dashboards',
                'manage_dashboards',
                'view_voyage_replay',
                'manage_users',
                'view_audit_logs',
                'manage_system_config',
                'view_system_health',
            ],
        }
        
        return permission in permissions.get(self.role, [])


class UserSession(TimeStampedModel):
    """
    Track active user sessions for security auditing
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token_jti = models.CharField(max_length=255, unique=True, db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token_jti', 'is_active']),
        ]
    
    def __str__(self):
        return f"Session for {self.user.email} from {self.ip_address}"


class AuditLog(TimeStampedModel):
    """
    Comprehensive audit logging for security and compliance
    """
    
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('export', 'Export'),
        ('config_change', 'Configuration Change'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    request_data = models.JSONField(default=dict, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self):
        return f"{self.user.email if self.user else 'Anonymous'} - {self.action} - {self.resource_type}"
