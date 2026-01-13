"""
URL routing for leaderboards app.
"""

from django.urls import path
from . import views

app_name = 'leaderboards'

urlpatterns = [
    # Overall leaderboard
    path('', views.overall_leaderboard, name='overall'),
    
    # Quiz-specific leaderboard
    path('quiz/<uuid:quiz_id>/', views.quiz_leaderboard, name='quiz-leaderboard'),
    
    # College leaderboard
    path('colleges/', views.college_leaderboard, name='colleges'),
    
    # User's position
    path('my-position/', views.my_position, name='my-position'),
]
