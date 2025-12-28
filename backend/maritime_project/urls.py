"""
Maritime Project URL Configuration
Centralized routing for all API endpoints
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# API Documentation Schema
schema_view = get_schema_view(
    openapi.Info(
        title="Maritime Vessel Tracking API",
        default_version='v1',
        description="""
        Complete API documentation for Maritime Vessel Tracking Platform
        
        **Features:**
        - Live vessel tracking with AIS integration
        - Port congestion analytics
        - Safety overlays (storms, piracy, accidents)
        - Historical voyage replay
        - Role-based dashboards (Operator, Analyst, Admin)
        - Real-time notifications
        
        **Authentication:**
        Use JWT Bearer token in Authorization header
        """,
        terms_of_service="https://www.maritimetracking.com/terms/",
        contact=openapi.Contact(email="api@maritimetracking.com"),
        license=openapi.License(name="Proprietary License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # API Endpoints
    path('api/auth/', include('apps.authentication.urls')),
    path('api/', include('apps.vessels.urls')),
    path('api/', include('apps.notifications.urls')),
    
    # Health Check
    path('api/health/', include('apps.core.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
