"""
URL routing for quizzes app.
"""

from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    # List and details
    path('categories/', views.list_categories, name='list-categories'),
    path('', views.quizzes_list, name='quizzes-list'),
    path('<uuid:quiz_id>/', views.quiz_detail, name='quiz-detail'),
    
    # Start quiz
    path('<uuid:quiz_id>/start/', views.start_quiz, name='start-quiz'),
    
    # User's attempts on a quiz
    path('<uuid:quiz_id>/attempts/', views.user_quiz_attempts, name='user-quiz-attempts'),
    
    # Attempt operations
    path('attempts/<uuid:attempt_id>/answer/', views.save_answer, name='save-answer'),
    path('attempts/<uuid:attempt_id>/submit/', views.submit_quiz, name='submit-quiz'),
    path('attempts/<uuid:attempt_id>/', views.get_results, name='get-results'),
    
    # User stats
    path('stats/', views.user_quiz_stats, name='user-quiz-stats'),
]
