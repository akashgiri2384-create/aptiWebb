"""
API views for XP system.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import logging

from .services import XPService, BadgeService

logger = logging.getLogger('quizzy')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    """
    GET /api/xp/stats/
    
    Get user's XP statistics.
    """
    stats = XPService.get_user_stats(request.user)
    
    return Response({
        'success': True,
        'data': stats
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def level_progress(request):
    """
    GET /api/xp/level-progress/
    
    Get user's level progress information.
    """
    progress = XPService.xp_to_next_level(request.user)
    
    return Response({
        'success': True,
        'data': progress
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def badges(request):
    """
    GET /api/xp/badges/
    
    Get user's earned badges.
    """
    user_badges = BadgeService.get_user_badges(request.user)
    
    return Response({
        'success': True,
        'data': {
            'badges': user_badges,
            'total': len(user_badges)
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def xp_logs(request):
    """
    GET /api/xp/logs/
    
    Get user's XP transaction history.
    
    Query params:
    - limit: Number of entries (default: 50)
    """
    from .models import XPLog
    
    limit = int(request.query_params.get('limit', 50))
    
    logs = XPLog.objects.filter(user=request.user).order_by('-created_at')[:limit]
    
    logs_data = [
        {
            'id': str(log.id),
            'amount': log.amount,
            'description': log.description,
            'transaction_type': log.transaction_type,
            'balance_after': log.balance_after,
            'created_at': log.created_at.isoformat(),
        }
        for log in logs
    ]
    
    return Response({
        'success': True,
        'data': {
            'logs': logs_data,
            'count': len(logs_data)
        }
    })
