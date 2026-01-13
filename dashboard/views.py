"""
API views for dashboard.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import logging

from .services import DashboardService

logger = logging.getLogger('quizzy')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    GET /api/dashboard/stats/
    
    Get user's dashboard statistics.
    """
    stats = DashboardService.get_user_stats(request.user)
    
    return Response({
        'success': True,
        'data': stats
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_activity(request):
    """
    GET /api/dashboard/activity/
    
    Get user's recent activity.
    
    Query params:
    - limit: Number of activities (default: 10)
    """
    limit = int(request.query_params.get('limit', 10))
    
    activities = DashboardService.get_recent_activities(request.user, limit=limit)
    
    return Response({
        'success': True,
        'data': {
            'activities': activities
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def weekly_stats(request):
    """
    GET /api/dashboard/weekly/
    
    Get weekly statistics.
    """
    weekly = DashboardService.get_weekly_stats(request.user)
    
    return Response({
        'success': True,
        'data': weekly
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def accuracy_trend(request):
    """
    GET /api/dashboard/accuracy-trend/
    
    Get accuracy trend data for charts.
    
    Query params:
    - days: Number of days (default: 30)
    """
    days = int(request.query_params.get('days', 30))
    
    trend = DashboardService.get_accuracy_trend(request.user, days=days)
    
    return Response({
        'success': True,
        'data': {
            'trend': trend
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leaderboard_view(request):
    """
    GET /api/dashboard/leaderboard/
    
    Get global or college leaderboard.
    
    Query params:
    - type: 'global' or 'college' (default: 'global')
    - limit: Number of users (default: 10)
    """
    from xp_system.services import XPService
    
    lb_type = request.query_params.get('type', 'global')
    limit = int(request.query_params.get('limit', 10))
    
    if lb_type == 'college':
        if not request.user.college:
            return Response({
                'success': False,
                'message': "You are not affiliated with any college."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        leaderboard = XPService.get_college_leaderboard(request.user.college, limit=limit, user=request.user)
    elif lb_type == 'colleges':
        leaderboard = XPService.get_college_rankings(limit=limit)
    else:
        leaderboard = XPService.get_global_leaderboard(limit=limit, user=request.user)
        
    return Response({
        'success': True,
        'data': {
            'type': lb_type,
            'leaderboard': leaderboard,
            'user_college': request.user.college.name if request.user.college else None
        }
    })
