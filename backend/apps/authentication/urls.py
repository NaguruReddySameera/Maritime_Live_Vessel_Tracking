from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.UserLoginView.as_view(), name='user-login'),
    path('register/', views.UserRegistrationView.as_view(), name='user-register'),
    path('logout/', views.UserLogoutView.as_view(), name='user-logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('demo-users/', views.DemoUsersView.as_view(), name='demo-users'),
    
    # User Profile
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('me/', views.UserProfileView.as_view(), name='user-me'),  # Alias for profile
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # User Management (Admin only)
    path('users/', views.UserManagementListView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserManagementDetailView.as_view(), name='user-detail'),
]
