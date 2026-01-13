"""
Global template context processors for Quizzy.

Provides site-wide variables available in all templates:
- Site name and settings
- User stats
- Feature flags
"""

from django.conf import settings


def site_context(request):
    """
    Add site-wide context variables to all templates.
    
    Returns:
        dict: Context dictionary with site settings
    """
    context = {
        'SITE_NAME': 'Quizzy',
        'SITE_TAGLINE': 'Master Your Skills, Compete & Win',
        'DEBUG': settings.DEBUG,
    }
    
    # Add user-specific context if authenticated
    if request.user.is_authenticated:
        context['user_is_admin'] = request.user.is_staff or request.user.is_superuser
    
    # Add Quizzy-specific settings
    if hasattr(settings, 'QUIZZY_SETTINGS'):
        context['QUIZZY_SETTINGS'] = settings.QUIZZY_SETTINGS
    
    return context
