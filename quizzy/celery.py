"""
Celery configuration for Quizzy platform.

This module configures Celery for background task processing including:
- XP distribution
- Leaderboard updates
- Report generation
- Ad fraud detection
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizzy.settings')

app = Celery('quizzy')

# Load configuration from Django settings, namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'reset-daily-quizzes': {
        'task': 'daily_quizzes.tasks.reset_daily_quizzes',
        'schedule': crontab(hour=0, minute=0),  # Midnight IST
        'options': {'expires': 3600},
    },
    'update-leaderboards': {
        'task': 'leaderboards.tasks.update_all_leaderboards',
        'schedule': 300.0,  # Every 5 minutes
        'options': {'expires': 60},
    },
    'generate-weekly-reports': {
        'task': 'analytics.tasks.generate_weekly_reports',
        'schedule': crontab(hour=20, minute=0, day_of_week='monday'),  # Monday 8 PM IST
        'options': {'expires': 3600},
    },
    'cleanup-fraudulent-ads': {
        'task': 'daily_quizzes.tasks.cleanup_fraudulent_ads',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'options': {'expires': 3600},
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')
