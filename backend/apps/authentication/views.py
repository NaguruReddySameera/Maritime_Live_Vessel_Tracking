"""
Authentication Views implementing the exact login flow:
1. Validate email format
2. Check user exists
3. Check account status (active/locked)
4. Verify password
5. Generate JWT tokens
"""

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
import logging

from .serializers import (
    UserLoginSerializer, UserRegistrationSerializer, UserProfileSerializer,
    ChangePasswordSerializer, UserListSerializer, UserManagementSerializer
)
from .models import AuditLog, UserSession
from .services import AuthenticationService
from .permissions import IsAdmin

User = get_user_model()
logger = logging.getLogger(__name__)


class UserLoginView(APIView):
    """
    User Login with comprehensive authentication flow
    
    Flow:
    1. Validate email format
    2. User lookup by email
    3. Check account status (is_active, is_locked)
    4. Verify password with Argon2
    5. Generate JWT tokens (access + refresh)
    6. Record login attempt (success/failure)
    7. Create user session
    8. Return tokens and user profile
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle user login"""
        serializer = UserLoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'message': 'Invalid input',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Step 1 & 2: Email validation and user lookup
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.warning(f"Login attempt with non-existent email: {email} from IP: {ip_address}")
            return Response({
                'success': False,
                'error': {
                    'message': 'Invalid email or password',
                    'code': 'INVALID_CREDENTIALS'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Step 3a: Check if account is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive account: {email}")
            return Response({
                'success': False,
                'error': {
                    'message': 'Account is deactivated. Please contact administrator.',
                    'code': 'ACCOUNT_INACTIVE'
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Step 3b: Check if account is locked
        if user.is_account_locked():
            lockout_remaining = (user.account_locked_until - timezone.now()).seconds // 60
            logger.warning(f"Login attempt for locked account: {email}")
            return Response({
                'success': False,
                'error': {
                    'message': f'Account is locked due to multiple failed login attempts. Try again in {lockout_remaining} minutes.',
                    'code': 'ACCOUNT_LOCKED',
                    'locked_until': user.account_locked_until.isoformat()
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Step 4: Verify password (Argon2 hashing)
        if not user.check_password(password):
            user.record_failed_login()
            logger.warning(f"Failed login attempt for {email} from IP: {ip_address}")
            
            remaining_attempts = settings.MAX_LOGIN_ATTEMPTS - user.failed_login_attempts
            error_message = 'Invalid email or password'
            
            if remaining_attempts > 0 and remaining_attempts <= 3:
                error_message += f'. {remaining_attempts} attempts remaining before account lockout.'
            
            return Response({
                'success': False,
                'error': {
                    'message': error_message,
                    'code': 'INVALID_CREDENTIALS'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Step 5: Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Reset failed login attempts on successful login
        user.reset_failed_logins()
        
        # Update user's last login info
        user.last_login = timezone.now()
        user.last_login_ip = ip_address
        user.last_activity = timezone.now()
        user.save(update_fields=['last_login', 'last_login_ip', 'last_activity'])
        
        # Step 6: Create user session for tracking
        UserSession.objects.create(
            user=user,
            token_jti=str(refresh['jti']),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=timezone.now() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
        )
        
        # Step 7: Log successful authentication
        AuditLog.objects.create(
            user=user,
            action='login',
            resource_type='authentication',
            description=f'User logged in successfully',
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(f"Successful login for {email} from IP: {ip_address}")
        
        # Step 8: Return response
        user_data = UserProfileSerializer(user).data
        
        return Response({
            'success': True,
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
                'user': user_data
            }
        }, status=status.HTTP_200_OK)
    
    def get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserRegistrationView(generics.CreateAPIView):
    """
    User registration endpoint - Open for anyone to register
    New users are created as inactive and require admin approval
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Create new user"""
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'message': 'Validation failed',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()
        
        # Auto-approve operators, require approval for analyst and admin roles
        if user.role == 'operator':
            user.is_active = True
            user.is_verified = True
            approval_status = 'auto-approved'
            message = 'Registration successful! You can now login.'
        else:
            # Analyst and Admin roles require admin approval
            user.is_active = False
            user.is_verified = False
            approval_status = 'pending approval'
            message = 'Registration successful! Your account is pending admin approval. You will be notified once approved.'
        
        user.save()
        
        # Log user creation
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action='create',
            resource_type='user',
            resource_id=str(user.id),
            description=f'New user registered ({approval_status}): {user.email} - Role: {user.role}',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'data': {
                'message': message,
                'user': UserProfileSerializer(user).data
            }
        }, status=status.HTTP_201_CREATED)
    
    def get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserLogoutView(APIView):
    """
    User logout - invalidate tokens and session
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Handle user logout"""
        try:
            # Get refresh token from request
            refresh_token = request.data.get('refresh_token')
            
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                
                # Deactivate user session
                UserSession.objects.filter(
                    user=request.user,
                    token_jti=str(token['jti'])
                ).update(is_active=False)
            
            # Log logout
            AuditLog.objects.create(
                user=request.user,
                action='logout',
                resource_type='authentication',
                description='User logged out',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            logger.info(f"User {request.user.email} logged out")
            
            return Response({
                'success': True,
                'data': {
                    'message': 'Logged out successfully'
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Logout error for {request.user.email}: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'message': 'Logout failed',
                    'details': str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get and update user profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Return current user"""
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        """Get user profile"""
        serializer = self.get_serializer(self.get_object())
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """Update user profile"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'message': 'Validation failed',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        # Log profile update
        AuditLog.objects.create(
            user=request.user,
            action='update',
            resource_type='user_profile',
            resource_id=str(request.user.id),
            description='Profile updated',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ChangePasswordView(APIView):
    """
    Change user password
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Change password"""
        serializer = ChangePasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'message': 'Validation failed',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        # Verify old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'success': False,
                'error': {
                    'message': 'Current password is incorrect'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.password_changed_at = timezone.now()
        user.save()
        
        # Log password change
        AuditLog.objects.create(
            user=user,
            action='update',
            resource_type='password',
            description='Password changed',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info(f"Password changed for user {user.email}")
        
        return Response({
            'success': True,
            'data': {
                'message': 'Password changed successfully'
            }
        })
    
    def get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Admin-only views
class UserManagementListView(generics.ListAPIView):
    """
    List all users (Admin only)
    """
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def get_queryset(self):
        """
        Filter users by status - show active by default, pending if requested
        """
        queryset = super().get_queryset()
        
        # Check for status filter
        status_filter = self.request.query_params.get('status', 'active')
        
        if status_filter == 'pending':
            # Show only pending approval users (inactive and not verified)
            queryset = queryset.filter(is_active=False)
        elif status_filter == 'active':
            # Show only active users
            queryset = queryset.filter(is_active=True)
        # 'all' would show everything (no filter)
            
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List users"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })


class UserManagementDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Manage specific user (Admin only)
    """
    queryset = User.objects.all()
    serializer_class = UserManagementSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def retrieve(self, request, *args, **kwargs):
        """Get user details"""
        serializer = self.get_serializer(self.get_object())
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """Update user"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': {
                    'message': 'Validation failed',
                    'details': serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        # Log user update
        AuditLog.objects.create(
            user=request.user,
            action='update',
            resource_type='user',
            resource_id=str(instance.id),
            description=f'User {instance.email} updated by admin',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Permanently delete user from database"""
        instance = self.get_object()
        user_email = instance.email
        user_id = instance.id
        
        # Protect default demo users from deletion
        protected_emails = [
                'sameerareddy583@gmail.com',
            'operator@maritimetracking.com'
        ]
        
        if user_email in protected_emails:
            return Response({
                'success': False,
                'error': {
                    'message': 'Cannot delete default system users. This user is protected.',
                    'code': 'PROTECTED_USER'
                }
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Log user deletion before removing
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            resource_type='user',
            resource_id=str(user_id),
            description=f'User {user_email} permanently deleted by admin',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Permanently delete the user
        instance.delete()
        
        return Response({
            'success': True,
            'data': {
                'message': 'User deleted successfully'
            }
        }, status=status.HTTP_200_OK)
    
    def get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DemoUsersView(APIView):
    """
    Get list of demo users for quick login
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Return demo user credentials"""
        demo_users = User.objects.filter(
            email__in=[
                'sameerareddy583@gmail.com',
                'analyst@maritimetracking.com',
                'operator@maritimetracking.com'
            ],
            is_active=True
        ).values('email', 'role', 'first_name', 'last_name')
        
        # Format response with hint about password pattern
        formatted_users = []
        password_hints = {
            'admin': 'admin',
            'analyst': 'Analyst@123',
            'operator': 'Operator@123'
        }
        for user in demo_users:
            formatted_users.append({
                'email': user['email'],
                'role': user['role'],
                'name': f"{user['first_name']} {user['last_name']}",
                'password_hint': password_hints.get(user['role'], f"{user['role'].capitalize()}@123")
            })
        
        return Response({
            'success': True,
            'data': formatted_users
        })
