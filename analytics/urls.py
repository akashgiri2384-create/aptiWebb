"""URL routing for analytics"""
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('platform/', views.platform_analytics, name='platform'),
    path('reports/weekly/', views.weekly_report, name='weekly'),
    # Additional URLs: reports/monthly/, reports/<id>/pdf/, college/, metrics/
]
