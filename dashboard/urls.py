"""
URL routing for dashboard.
"""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard stats
    path('stats/', views.dashboard_stats, name='stats'),
    
    # Recent activity
    path('activity/', views.recent_activity, name='activity'),
    
    # Weekly stats
    path('weekly/', views.weekly_stats, name='weekly'),
    
    # Accuracy trend
    path('accuracy-trend/', views.accuracy_trend, name='accuracy-trend'),
    
    # Leaderboard
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
]
