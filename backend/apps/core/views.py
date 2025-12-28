"""
Health check endpoints
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection
from django.core.cache import cache
import redis
from django.conf import settings


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Basic health check endpoint
    """
    return Response({
        'status': 'healthy',
        'service': 'Maritime Vessel Tracking API',
        'version': '1.0.0'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check - verifies all dependencies
    """
    health_status = {
        'status': 'ready',
        'checks': {}
    }
    
    # Check database connection
    try:
        connection.ensure_connection()
        health_status['checks']['database'] = 'connected'
    except Exception as e:
        health_status['checks']['database'] = f'error: {str(e)}'
        health_status['status'] = 'not_ready'
    
    # Check Redis connection
    try:
        r = redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
        health_status['checks']['redis'] = 'connected'
    except Exception as e:
        health_status['checks']['redis'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'
    
    return Response(health_status)
