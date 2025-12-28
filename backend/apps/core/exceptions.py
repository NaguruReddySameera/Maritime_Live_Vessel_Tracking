"""
Custom exception handler for DRF
Provides consistent error response format
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the response data
        custom_response_data = {
            'success': False,
            'error': {
                'message': str(exc),
                'details': response.data if isinstance(response.data, dict) else {'detail': response.data}
            }
        }
        
        # Log the error
        logger.error(
            f"API Error: {exc.__class__.__name__} - {str(exc)}",
            extra={
                'status_code': response.status_code,
                'view': context.get('view').__class__.__name__ if context.get('view') else None,
                'request': context.get('request').path if context.get('request') else None
            }
        )
        
        response.data = custom_response_data
    else:
        # Handle non-DRF exceptions
        logger.error(
            f"Unhandled Exception: {exc.__class__.__name__} - {str(exc)}",
            exc_info=True
        )
        
        response = Response(
            {
                'success': False,
                'error': {
                    'message': 'Internal server error',
                    'details': str(exc) if hasattr(exc, '__str__') else 'An unexpected error occurred'
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response
