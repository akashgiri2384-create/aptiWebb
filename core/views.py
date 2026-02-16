from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.management import call_command
from django.conf import settings
from rest_framework import status
import logging

logger = logging.getLogger('django')

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def cleanup_logs_view(request):
    """
    Trigger database cleanup manually or via external cron.
    Protected by a secret key in query param: ?key=YOUR_SECRET_KEY
    """
    secret_key = request.GET.get('key')
    
    # Simple protection mechanism
    # In production, use a strong random string stored in env
    expected_key = getattr(settings, 'CLEANUP_SECRET_KEY', 'default-cleanup-key-123')
    
    if secret_key != expected_key:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
    try:
        call_command('cleanup_logs')
        return Response({'success': True, 'message': 'Cleanup completed successfully.'})
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def error_404(request, exception):
    from django.http import JsonResponse
    return JsonResponse({'error': 'Not Found'}, status=404)

def error_500(request):
    from django.http import JsonResponse
    return JsonResponse({'error': 'Server Error'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_api(request):
    """
    POST /api/chat/ask/

    Prof. Curio AI chatbot endpoint.
    Accepts: { "message": "...", "history": [...] }
    Returns: { "success": true, "reply": "..." }
    """
    from .chatbot_service import ChatbotService

    message = request.data.get('message', '').strip()
    if not message:
        return Response({
            'success': False,
            'error': 'Message is required.'
        }, status=status.HTTP_400_BAD_REQUEST)

    history = request.data.get('history', [])

    success, reply, error = ChatbotService.get_response(message, history)

    if success:
        return Response({
            'success': True,
            'reply': reply
        })
    else:
        return Response({
            'success': False,
            'error': error
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
