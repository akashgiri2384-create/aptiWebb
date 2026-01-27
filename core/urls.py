"""
URL routing for core app.
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('disclaimer/', views.disclaimer, name='disclaimer'),
    path('system/cleanup/', views.cleanup_logs_view, name='cleanup_logs'),
]
