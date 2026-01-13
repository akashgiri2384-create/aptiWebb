"""
Frontend views for serving HTML templates.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def login_page(request):
    """Render login page"""
    return render(request, 'auth/login.html')


def register_page(request):
    """Render register page"""
    return render(request, 'auth/register.html')


def quiz_list_page(request):
    """Render quiz list page"""
    return render(request, 'quizzes/list.html')


def take_quiz_page(request, attempt_id):
    """Render quiz taking page"""
    return render(request, 'quizzes/take_quiz.html')


def quiz_result_page(request, attempt_id):
    """Render quiz result page"""
    from quizzes.models import QuizAttempt
    from dashboard.models import UserActivityLog
    from django.utils import timezone
    from datetime import timedelta
    
    context = {}
    
    if request.user.is_authenticated:
        # Get attempt data
        try:
            attempt = QuizAttempt.objects.get(id=attempt_id, user=request.user)
            context['attempt'] = attempt
            context['score'] = attempt.percentage_score
            context['quiz'] = attempt.quiz
            context['passed'] = attempt.is_passed
            context['questions_total'] = attempt.total_questions
            context['correct_count'] = attempt.correct_count
            context['wrong_count'] = attempt.wrong_count
            context['accuracy'] = attempt.percentage_score
        except QuizAttempt.DoesNotExist:
            pass
            
        # Check for recent rank up (last 2 minutes)
        # We check for a Rank Up activity that might have been created by the quiz submission
        recent_rank_up = UserActivityLog.objects.filter(
            user=request.user,
            activity_type='rank_up',
            created_at__gte=timezone.now() - timedelta(minutes=2) 
        ).first()
        
        if recent_rank_up:
            context['rank_up'] = recent_rank_up
            
    return render(request, 'quizzes/result.html', context)


def leaderboard_page(request):
    """Render leaderboard page"""
    return render(request, 'leaderboard/index.html')


def profile_page(request):
    """Render profile page"""
    return render(request, 'accounts/profile.html')


def home_page(request):
    """Render home page"""
    if request.user.is_authenticated:
        return render(request, 'quizzes/list.html')
    return render(request, 'auth/login.html')
