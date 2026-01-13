"""
URL routing for XP system.
"""

from django.urls import path
from . import views

app_name = 'xp_system'

urlpatterns = [
    # User stats
    path('stats/', views.user_stats, name='stats'),
    
    # Level progress
    path('level-progress/', views.level_progress, name='level-progress'),
    
    # Badges
    path('badges/', views.badges, name='badges'),
    
    # XP logs
    path('logs/', views.xp_logs, name='logs'),
]
