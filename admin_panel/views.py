"""
API views for admin panel.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import logging

from .services import AdminService
from .models import AdminUser

logger = logging.getLogger('quizzy')


def is_admin(user):
    """Check if user is an admin"""
    try:
        return hasattr(user, 'admin_user') and user.admin_user.is_active
    except:
        return False


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    GET /api/admin-panel/stats/
    
    Get admin dashboard statistics.
    """
    if not is_admin(request.user):
        return Response({
            'success': False,
            'error': {'message': 'Admin access required'}
        }, status=status.HTTP_403_FORBIDDEN)
    
    stats = AdminService.get_dashboard_stats()
    
    return Response({
        'success': True,
        'data': stats
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_user(request, user_id):
    """
    POST /api/admin-panel/users/<user_id>/approve/
    
    Approve a user.
    """
    if not is_admin(request.user):
        return Response({
            'success': False,
            'error': {'message': 'Admin access required'}
        }, status=status.HTTP_403_FORBIDDEN)
    
    notes = request.data.get('notes')
    
    success, message = AdminService.approve_user(
        admin_user=request.user.admin_user,
        user_id=user_id,
        notes=notes
    )
    
    if not success:
        return Response({
            'success': False,
            'error': {'message': message}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': True,
        'message': message
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ban_user(request, user_id):
    """
    POST /api/admin-panel/users/<user_id>/ban/
    
    Ban a user.
    
    Body:
    {
        "reason": "Violation of terms",
        "duration_days": 30  // optional
    }
    """
    if not is_admin(request.user):
        return Response({
            'success': False,
            'error': {'message': 'Admin access required'}
        }, status=status.HTTP_403_FORBIDDEN)
    
    reason = request.data.get('reason')
    duration_days = request.data.get('duration_days')
    
    if not reason:
        return Response({
            'success': False,
            'error': {'message': 'Reason is required'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    success, message = AdminService.ban_user(
        admin_user=request.user.admin_user,
        user_id=user_id,
        reason=reason,
        duration_days=duration_days
    )
    
    if not success:
        return Response({
            'success': False,
            'error': {'message': message}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': True,
        'message': message
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def grant_xp(request, user_id):
    """
    POST /api/admin-panel/users/<user_id>/grant-xp/
    
    Grant XP to a user.
    
    Body:
    {
        "amount": 100,
        "description": "Special achievement"
    }
    """
    if not is_admin(request.user):
        return Response({
            'success': False,
            'error': {'message': 'Admin access required'}
        }, status=status.HTTP_403_FORBIDDEN)
    
    amount = request.data.get('amount')
    description = request.data.get('description')
    
    if not amount or not description:
        return Response({
            'success': False,
            'error': {'message': 'Amount and description are required'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    success, message = AdminService.grant_xp(
        admin_user=request.user.admin_user,
        user_id=user_id,
        amount=int(amount),
        description=description
    )
    
    if not success:
        return Response({
            'success': False,
            'error': {'message': message}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': True,
        'message': message
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_quizzes(request):
    """
    POST /api/admin-panel/quizzes/import/
    
    Import quizzes from CSV.
    
    Form data:
    - file: CSV file
    - category_id: UUID of category
    """
    if not is_admin(request.user):
        return Response({
            'success': False,
            'error': {'message': 'Admin access required'}
        }, status=status.HTTP_403_FORBIDDEN)
    
    csv_file = request.FILES.get('file')
    category_id = request.data.get('category_id')
    
    if not csv_file or not category_id:
        return Response({
            'success': False,
            'error': {'message': 'File and category_id are required'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    success, imported_count, errors = AdminService.import_quizzes_csv(
        admin_user=request.user.admin_user,
        csv_file=csv_file,
        category_id=category_id
    )
    
    return Response({
        'success': success,
        'data': {
            'imported_count': imported_count,
            'errors': errors
        }
    })
