"""
API views for leaderboards app.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
import logging

from .services import LeaderboardService

logger = logging.getLogger('quizzy')


@api_view(['GET'])
@permission_classes([AllowAny])
def overall_leaderboard(request):
    """
    GET /api/leaderboards/
    
    Get overall leaderboard.
    
    Query params:
    - scope: all_time/weekly/monthly (default: all_time)
    - limit: Number of entries (default: 100)
    """
    scope = request.query_params.get('scope', 'all_time')
    limit = int(request.query_params.get('limit', 100))
    
    leaderboard = LeaderboardService.calculate_overall_leaderboard(
        scope=scope,
        limit=limit
    )
    
    return Response({
        'success': True,
        'data': {
            'leaderboard': leaderboard,
            'scope': scope,
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def quiz_leaderboard(request, quiz_id):
    """
    GET /api/leaderboards/quiz/<quiz_id>/
    
    Get leaderboard for specific quiz.
    """
    limit = int(request.query_params.get('limit', 50))
    
    leaderboard = LeaderboardService.calculate_quiz_leaderboard(
        quiz_id=quiz_id,
        limit=limit
    )
    
    return Response({
        'success': True,
        'data': {
            'leaderboard': leaderboard,
            'quiz_id': str(quiz_id),
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def college_leaderboard(request):
    """
    GET /api/leaderboards/colleges/
    
    Get college-wise leaderboard.
    """
    limit = int(request.query_params.get('limit', 50))
    
    leaderboard = LeaderboardService.calculate_college_leaderboard(limit=limit)
    
    return Response({
        'success': True,
        'data': {
            'leaderboard': leaderboard
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_position(request):
    """
    GET /api/leaderboards/my-position/
    
    Get current user's position in leaderboard.
    """
    scope = request.query_params.get('scope', 'all_time')
    
    position = LeaderboardService.get_user_position(
        user=request.user,
        scope=scope
    )
    
    return Response({
        'success': True,
        'data': position
    })
