"""
API views for daily quizzes.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import logging

from .services import DailyQuizService, KeyService

logger = logging.getLogger('quizzy')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def today_quizzes(request):
    """
    GET /api/daily-quizzes/today/
    
    Get today's daily quizzes list.
    """
    daily_quizzes = list(DailyQuizService.get_today_quizzes())
    
    # Sort: Morning -> Evening -> Night
    slot_order = {'morning': 1, 'evening': 2, 'night': 3}
    daily_quizzes.sort(key=lambda x: slot_order.get(x.slot, 99))
    
    data = []
    for dq in daily_quizzes:
        is_unlocked, unlock_record = DailyQuizService.check_unlock_status(request.user, dq)
        
        data.append({
            'id': str(dq.id),
            'quiz_id': str(dq.quiz.id) if dq.quiz else None,
            'title': dq.quiz.title if dq.quiz else dq.quiz_title,
            'date': dq.date.isoformat(),
            'slot': dq.slot,
            'slot_display': dq.get_slot_display(),
            'difficulty': dq.difficulty,
            'keys_required': dq.keys_required,
            'keys_earned': unlock_record.keys_earned if unlock_record else 0, # NEW: Send local progress
            'xp_multiplier': dq.xp_multiplier,
            'is_unlocked': is_unlocked,
            'is_completed': dq.quiz.attempts.filter(user=request.user).exists() if dq.quiz else False,
            'total_questions': dq.quiz.questions.count() if dq.quiz else 0, # NEW: Dynamic Question Count
        })
    
    return Response({
        'success': True,
        'data': {
            'quizzes': data
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlock_quiz(request):
    """
    POST /api/daily-quizzes/unlock/
    
    Unlock a daily quiz with keys.
    Body: { "daily_quiz_id": "UUID" }
    """
    daily_quiz_id = request.data.get('daily_quiz_id')
    
    if not daily_quiz_id:
        return Response({
            'success': False,
            'error': {'message': 'daily_quiz_id is required'}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    success, message = DailyQuizService.unlock_with_keys(
        user=request.user,
        daily_quiz_id=daily_quiz_id
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
def watch_ad(request):
    """
    POST /api/daily-quizzes/watch-ad/
    
    Watch ad to earn keys (local to quiz if ID provided, else global fallback?).
    Body: { "daily_quiz_id": "UUID" (optional but recommended) }
    """
    daily_quiz_id = request.data.get('daily_quiz_id')
    
    success, message, keys_earned = DailyQuizService.watch_ad_for_key(
        user=request.user,
        daily_quiz_id=daily_quiz_id
    )
    
    if not success:
        return Response({
            'success': False,
            'error': {'message': message}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': True,
        'data': {
            'keys_earned': keys_earned,
            # 'total_keys': ... No longer relevant if local?
            # actually let's return new local balance if possible?
            # Service should return it.
        },
        'message': message
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def key_balance(request):
    """
    GET /api/daily-quizzes/keys/
    
    Get user's key balance.
    """
    balance = KeyService.get_available_keys(request.user)
    
    return Response({
        'success': True,
        'data': {
            'available_keys': balance
        }
    })
