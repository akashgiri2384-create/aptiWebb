"""
WSGI config for Quizzy project.

Exposes the WSGI callable as a module-level variable named ``application``.
Used by Gunicorn and other WSGI servers.
"""

import os
import socket
from django.core.wsgi import get_wsgi_application

# --- KEY FIX FOR RAILWAY/RENDER ---
# Force IPv4 Resolution to fix Gmail SMTP Timeouts
# Many containers default to IPv6 which Gmail drops/times out on.
allowed_gai_family = socket.AF_INET

def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    # Retrieve the real family for the request
    if family == 0:
        family = allowed_gai_family
    return _original_getaddrinfo(host, port, family, type, proto, flags)

_original_getaddrinfo = socket.getaddrinfo
socket.getaddrinfo = _patched_getaddrinfo
# ----------------------------------

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizzy.settings')

application = get_wsgi_application()
