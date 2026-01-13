"""
URL routing for admin panel.
"""

from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('stats/', views.dashboard_stats, name='stats'),
    
    # User management
    path('users/<uuid:user_id>/approve/', views.approve_user, name='approve-user'),
    path('users/<uuid:user_id>/ban/', views.ban_user, name='ban-user'),
    path('users/<uuid:user_id>/grant-xp/', views.grant_xp, name='grant-xp'),
    
    # Quiz import
    path('quizzes/import/', views.import_quizzes, name='import-quizzes'),
]
