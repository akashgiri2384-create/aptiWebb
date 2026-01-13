"""
Custom middleware for Quizzy platform.
"""

import logging
import time
from django.http import JsonResponse

logger = logging.getLogger('quizzy')
performance_logger = logging.getLogger('performance')


class ErrorHandlingMiddleware:
    """
    Global error handling middleware.
    
    Catches unhandled exceptions and returns proper JSON responses.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """Handle unhandled exceptions."""
        logger.error(f'Unhandled exception: {str(exception)}', exc_info=True)
        
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again later.',
            'error': str(exception) if request.user.is_staff else None
        }, status=500)


class PerformanceMonitoringMiddleware:
    """
    Monitor response times and log slow requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Log slow requests (> 500ms)
        if duration > 0.5:
            performance_logger.warning(
                f'Slow request: {request.path} took {duration:.2f}s'
            )
        
        # Add response time header
        response['X-Response-Time'] = f'{duration:.3f}s'
        
        return response
