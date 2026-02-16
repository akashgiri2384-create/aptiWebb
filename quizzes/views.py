"""
API views for quizzes app.

Endpoints:
- GET /api/quizzes/ - List all quizzes with filters
- GET /api/quizzes/<quiz_id>/ - Get quiz details  
- POST /api/quizzes/<quiz_id>/start/ - Start quiz attempt
- POST /api/quizzes/attempts/<attempt_id>/answer/ - Save answer
- POST /api/quizzes/attempts/<attempt_id>/submit/ - Submit quiz
- GET /api/quizzes/attempts/<attempt_id>/ - Get quiz results
- GET /api/quizzes/<quiz_id>/attempts/ - Get user's attempts on quiz
- GET /api/quizzes/stats/ - Get user's quiz stats
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
import logging

from .services import QuizService, RecommendationService

logger = logging.getLogger('quizzy')


@api_view(['GET'])
@permission_classes([AllowAny])
def quizzes_list(request):
    """
    GET /api/quizzes/
    
    List all published quizzes with optional filters.
    
    Query params:
    - category: Category slug
    - difficulty: easy/medium/hard
    - limit: Results limit (default: 20)
    - offset: Results offset (default: 0)
    """
    try:
        user = request.user if request.user.is_authenticated else None
        
        data = QuizService.get_quizzes_list(
            category=request.query_params.get('category'),
            difficulty=request.query_params.get('difficulty'),
            user=user,
            limit=int(request.query_params.get('limit', 20)),
            offset=int(request.query_params.get('offset', 0))
        )
        
        return Response({
            'success': True,
            'data': data
        })
    
    except Exception as e:
        logger.error(f"Error listing quizzes: {str(e)}")
        return Response({
            'success': False,
            'error': {'message': 'Failed to load quizzes'}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def quiz_detail(request, quiz_id):
    """
    GET /api/quizzes/<quiz_id>/
    
    Get detailed information about a specific quiz.
    """
    user = request.user if request.user.is_authenticated else None
    success, data, error = QuizService.get_quiz_details(quiz_id, user)
    
    if not success:
        return Response({
            'success': False,
            'error': {'message': error}
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'success': True,
        'data': data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_quiz(request, quiz_id):
    """
    POST /api/quizzes/<quiz_id>/start/
    
    Start a new quiz attempt.
    """
    success, data, error = QuizService.start_quiz(request.user, quiz_id)
    
    if not success:
        return Response({
            'success': False,
            'error': {'message': error}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': True,
        'data': data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_answer(request, attempt_id):
    """
    POST /api/quizzes/attempts/<attempt_id>/answer/
    
    Save user's answer to a question.
    
    Request body:
    {
        "question_id": "uuid",
        "selected_answer": "A"  // A, B, C, or D
    }
    """
    question_id = request.data.get('question_id')
    selected_answer = request.data.get('selected_answer')
    
    if not question_id or not selected_answer:
        return Response({
            'success': False,
            'error': {'message': 'question_id and selected_answer are required'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    success, data, error = QuizService.save_answer(
        attempt_id,
        question_id,
        selected_answer
    )
    
    if not success:
        return Response({
            'success': False,
            'error': {'message': error}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': True,
        'data': data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_quiz(request, attempt_id):
    """
    POST /api/quizzes/attempts/<attempt_id>/submit/
    
    Submit quiz for grading.
    """
    success, data, error = QuizService.submit_quiz(attempt_id)
    
    if not success:
        return Response({
            'success': False,
            'error': {'message': error}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': True,
        'data': data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_results(request, attempt_id):
    """
    GET /api/quizzes/attempts/<attempt_id>/
    
    Get detailed results for a quiz attempt.
    """
    success, data, error = QuizService.get_quiz_results(attempt_id, request.user)
    
    # If failed because not graded, try getting active context
    if not success and error == "Quiz not yet graded":
        success, data, error = QuizService.get_attempt_context(attempt_id, request.user)
    
    if not success:
        return Response({
            'success': False,
            'error': {'message': error}
        }, status=status.HTTP_403_FORBIDDEN if error == "Unauthorized" else status.HTTP_404_NOT_FOUND)
    
    return Response({
        'success': True,
        'data': data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_quiz_attempts(request, quiz_id):
    """
    GET /api/quizzes/<quiz_id>/attempts/
    
    Get all user's attempts on a specific quiz.
    """
    from .models import QuizAttempt
    
    attempts = QuizAttempt.objects.filter(
        quiz_id=quiz_id,
        user=request.user
    ).order_by('-started_at')[:10]
    
    attempts_data = [
        {
            'id': str(attempt.id),
            'status': attempt.status,
            'score': attempt.percentage_score,
            'passed': attempt.is_passed,
            'xp_earned': attempt.xp_earned,
            'started_at': attempt.started_at.isoformat(),
            'submitted_at': attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        }
        for attempt in attempts
    ]
    
    return Response({
        'success': True,
        'data': {'attempts': attempts_data}
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_quiz_stats(request):
    """
    GET /api/quizzes/stats/
    
    Get user's overall quiz statistics.
    """
    stats = QuizService.user_quiz_stats(request.user)
    
    return Response({
        'success': True,
        'data': stats
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def list_categories(request):
    """
    GET /api/quizzes/categories/
    
    List all active categories.
    """
    from .models import Category
    
    categories = Category.objects.filter(is_active=True).order_by('order', 'name')
    
    data = [
        {
            'id': str(cat.id),
            'name': cat.name,
            'slug': cat.slug,
            'icon': cat.icon,
            'emoji': cat.emoji,
            'color': cat.color,
            'total_quizzes': cat.total_quizzes
        }
        for cat in categories
    ]
    
    return Response({
        'success': True,
        'data': data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_recommendations(request):
    """
    GET /api/quizzes/recommendations/

    Get AI-powered personalized quiz recommendations.

    Returns quizzes tailored to the user's weak areas, unexplored
    categories, and challenge suggestions based on quiz history.
    """
    try:
        limit = int(request.query_params.get('limit', 6))
        data = RecommendationService.get_recommendations(request.user, limit=limit)

        return Response({
            'success': True,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return Response({
            'success': False,
            'error': {'message': 'Failed to generate recommendations'}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
