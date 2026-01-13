"""
ASGI config for Quizzy project.

Exposes the ASGI callable as a module-level variable named ``application``.
Used for async Django applications.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizzy.settings')

application = get_asgi_application()
