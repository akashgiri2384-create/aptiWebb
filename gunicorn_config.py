"""
Gunicorn configuration for production deployment.

Optimized for 10,000+ concurrent users.
"""

import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
# Worker processes
# optimized for 512MB RAM (Starter Plan)
# Do not use multiprocessing.cpu_count() in shared/small containers
workers = 2 
worker_class = 'gthread'  # Use threads for better I/O handling
threads = 4
worker_connections = 1000
timeout = 120
keepalive = 5

# Restart workers
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'quizzy'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None
