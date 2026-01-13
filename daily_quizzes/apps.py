"""
Daily Quizzes Application Configuration
"""
from django.apps import AppConfig


class DailyQuizzesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'daily_quizzes'
    verbose_name = 'Daily Quizzes & Keys'
