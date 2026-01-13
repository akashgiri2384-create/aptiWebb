"""
URL routing for daily quizzes.
"""

from django.urls import path
from . import views

app_name = 'daily_quizzes'

urlpatterns = [
    # Today's quiz
    path('today/', views.today_quizzes, name='today'),
    
    # Unlock quiz
    path('unlock/', views.unlock_quiz, name='unlock'),
    
    # Watch ad for keys
    path('watch-ad/', views.watch_ad, name='watch-ad'),
    
    # Key balance
    path('keys/', views.key_balance, name='keys'),
]
