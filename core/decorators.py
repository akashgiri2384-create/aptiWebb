"""
Custom decorators for Quizzy platform.
"""

from functools import wraps
from django.http import JsonResponse
from rest_framework import status


def handle_exceptions(func):
    """
    Decorator to handle exceptions in view functions.
    
    Returns JSON response for exceptions.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return wrapper


def require_verification(func):
    """
    Decorator to require email verification.
    
    Checks if user's email is verified before allowing access.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not request.user.is_email_verified:
            return JsonResponse({
                'success': False,
                'message': 'Email verification required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return func(request, *args, **kwargs)
    return wrapper
