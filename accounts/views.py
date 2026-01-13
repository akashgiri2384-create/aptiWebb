"""
API views for accounts app.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
import logging

from .services import AuthService, ProfileService, SessionService
from .serializers import (
    SignupSerializer, LoginSerializer, PasswordChangeSerializer,
    ProfileUpdateSerializer, UserSerializer, UserProfileSerializer
)

# OTP Imports
from rest_framework.views import APIView
from django.utils import timezone
from .models import OTPVerification, CustomUser
from .serializers import SendOTPSerializer, VerifyOTPSerializer, ResetPasswordSerializer
from .otp_utils import OTPManager
from .email_service import EmailService

logger = logging.getLogger('quizzy')


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def register(request):
    """
    POST /api/accounts/register/
    
    Register a new user.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "password123",
        "full_name": "John Doe",
        "college_id": "uuid",
        "year": 2,
        "branch": "Computer Science",
        "roll_number": "CS2021001",
        "mobile_number": "+911234567890",
        "accepted_terms": true,
        "accepted_privacy": true
    }
    """
    serializer = SignupSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {'message': 'Validation failed', 'details': serializer.errors}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    success, result = AuthService.register_user(
        email=serializer.validated_data['email'],
        password=serializer.validated_data['password'],
        full_name=serializer.validated_data['full_name'],
        college=serializer.validated_data.get('college_name'),
        year=serializer.validated_data.get('year'),
        branch=serializer.validated_data.get('branch'),
        roll_number=serializer.validated_data.get('roll_number'),
        mobile_number=serializer.validated_data.get('mobile_number'),
        accepted_terms=serializer.validated_data.get('accepted_terms'),
        accepted_privacy=serializer.validated_data.get('accepted_privacy'),
    )
    
    if not success:
        return Response({
            'success': False,
            'error': {'message': result}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': True,
        'data': result
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    GET /api/accounts/verify-email?token=...
    Verify user email via link.
    """
    token = request.query_params.get('token')
    if not token:
        return Response({'success': False, 'message': 'Token missing'}, status=400)
        
    success, message = AuthService.verify_email_token(token)
    
    from django.shortcuts import render
    return render(request, 'auth/verify_email.html', {
        'success': success,
        'message': message
    })





# --- Pre-Registration Views ---

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def initiate_verification(request):
    """Send verification link before registration"""
    email = request.data.get('email')
    full_name = request.data.get('full_name', 'User')
    
    if not email:
        return Response({'success': False, 'message': 'Email is required'}, status=400)
    
    success, msg = AuthService.initiate_email_verification(email, full_name)
    if success:
         return Response({'success': True, 'message': 'Verification link sent.'})
    else:
         return Response({'success': False, 'message': msg}, status=400)

@api_view(['GET'])
@permission_classes([AllowAny])
def check_verification_status(request):
    """Check if email is verified"""
    email = request.query_params.get('email')
    if not email: return Response({'success': False, 'verified': False})
    
    is_verified = AuthService.check_verification_status(email)
    return Response({'success': True, 'verified': is_verified})

@api_view(['GET'])
@permission_classes([AllowAny])

def confirm_email(request):
    """Link target for pre-registration"""
    token = request.query_params.get('token')
    success, message, email = AuthService.confirm_email_token(token)
    
    from django.shortcuts import render, redirect
    
    if success:
        # return redirect(f'/register?verified=true&email={email}')
        return render(request, 'auth/verification_success_popup.html', {'email': email})
    
    # On failure, show error page
    return render(request, 'auth/verify_email.html', {
        'success': success,
        'message': message
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def login(request):
    """
    POST /api/accounts/login/
    
    Login user and return JWT tokens.
    
    Request body:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {'message': 'Validation failed', 'details': serializer.errors}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    success, data, message = AuthService.login_user(
        email=serializer.validated_data['email'],
        password=serializer.validated_data['password'],
        request=request
    )
    
    if not success:
        return Response({
            'success': False,
            'error': {'message': message}
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response({
        'success': True,
        'data': data,
        'message': message
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    POST /api/accounts/logout/
    
    Logout current user.
    """
    success, message = AuthService.logout_user(request.user)
    
    return Response({
        'success': success,
        'message': message
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    GET /api/accounts/profile/
    
    Get current user's profile.
    """
    profile_data = ProfileService.get_profile(request.user)
    
    return Response({
        'success': True,
        'data': profile_data
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    PUT /api/accounts/profile/
    
    Update current user's profile.
    """
    success, message = ProfileService.update_profile(request.user, request.data)
    
    if not success:
        return Response({
            'success': False,
            'error': {'message': message}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Return updated profile
    profile_data = ProfileService.get_profile(request.user)
    
    return Response({
        'success': True,
        'data': profile_data,
        'message': message
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    POST /api/accounts/change-password/
    
    Change user password.
    
    Request body:
    {
        "old_password": "current123",
        "new_password": "newpassword123"
    }
    """
    serializer = PasswordChangeSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {'message': 'Validation failed', 'details': serializer.errors}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    success, message = AuthService.change_password(
        user=request.user,
        old_password=serializer.validated_data['old_password'],
        new_password=serializer.validated_data['new_password']
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sessions(request):
    """
    GET /api/accounts/sessions/
    
    Get user's active sessions.
    """
    active_sessions = SessionService.get_active_sessions(request.user)
    
    sessions_data = [
        {
            'id': str(session.id),
            'device_type': session.device_type,
            'ip_address': session.ip_address,
            'login_at': session.login_at.isoformat(),
            'last_activity': session.last_activity.isoformat() if session.last_activity else None,
        }
        for session in active_sessions
    ]
    
    return Response({
        'success': True,
        'data': {'sessions': sessions_data}
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def colleges_list(request):
    """
    GET /api/accounts/colleges/
    
    Get list of all active colleges.
    """
    from .models import College
    from .serializers import CollegeSerializer
    
    colleges = College.objects.filter(is_active=True).order_by('name')
    
    # Search filter
    search = request.query_params.get('search', '').strip()
    if search:
        colleges = colleges.filter(name__icontains=search)
    
    serializer = CollegeSerializer(colleges, many=True)
    
    return Response({
        'success': True,
        'data': serializer.data,
        'count': colleges.count()
    })


class SendOTPView(APIView):
    """Send OTP to email for password reset"""
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        
        if not serializer.is_valid():
            # Get first error message
            first_error = next(iter(serializer.errors.values()))[0] if serializer.errors else 'Invalid data'
            if isinstance(first_error, dict): # Handle nested errors if any
                first_error = str(first_error)
                
            return Response(
                {
                    'success': False,
                    'error': {'message': first_error}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        otp_type = serializer.validated_data['type']
        
        # Check if user exists
        if not CustomUser.objects.filter(email=email).exists():
            return Response(
                {
                    'success': False,
                    'error': {'message': 'Account does not exist'}
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Generate OTP
            otp = OTPManager.generate_otp()
            otp_hash = OTPManager.hash_otp(otp)
            
            # Create OTP record
            OTPVerification.objects.create(
                email=email,
                otp_hash=otp_hash,
                type=otp_type,
                expires_at=OTPManager.get_otp_expiry(),
            )
            
            # Send OTP synchronously (since celery might not be running in this env yet)
            # In production, this should be a celery task: send_otp_email_task.delay(email, otp, otp_type)
            EmailService.send_otp_email(email, otp, otp_type)
            
            logger.info(f"OTP sent to {email} for {otp_type}")
            
            # Generic response (don't reveal if email exists) - WAIT, user requested to reveal it if NOT exists
            # So if we are here, it exists.
            return Response(
                {
                    'success': True,
                    'message': 'OTP sent successfully.', 
                    'info': 'Please check your email and spam folder.'
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error sending OTP: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': 'An error occurred while sending OTP.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VerifyOTPView(APIView):
    """Verify OTP before password reset"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0] if serializer.errors else 'Invalid data'
            return Response(
                {
                    'success': False,
                    'error': {'message': first_error}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        otp_type = serializer.validated_data['type']
        
        try:
            # Get latest OTP for this email
            otp_record = OTPVerification.objects.filter(
                email=email,
                type=otp_type,
                is_used=False
            ).latest('created_at')
            
            # Check if can verify
            if not otp_record.can_verify():
                if otp_record.is_expired():
                    return Response(
                        {'error': 'OTP has expired. Please request a new one.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    return Response(
                        {'error': 'Maximum verification attempts exceeded. Please request a new OTP.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Verify OTP
            if not OTPManager.verify_otp_hash(otp, otp_record.otp_hash):
                otp_record.increment_attempts()
                remaining = otp_record.max_attempts - otp_record.attempts
                return Response(
                    {'error': f'Invalid OTP. {remaining} attempts remaining.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark as used (in this flow, we mark it used here to confirm validity)
            # However, strictly for password reset, we might want to keep it 'unused' until password is reset,
            # or use a temp token. For simplicity here, we verify it here and let the client proceed.
            # BUT, `ResetPasswordView` needs to verify it again. So we WON'T mark it used here if it's for PASSWORD_RESET.
            # We will just return success. It will be marked used in ResetPasswordView.
            
            if otp_type != 'PASSWORD_RESET':
                 otp_record.mark_used()
            
            logger.info(f"OTP verified for {email}")
            
            return Response(
                {
                    'success': True,
                    'message': 'OTP verified successfully.',
                    'verified': True
                },
                status=status.HTTP_200_OK
            )
            
        except OTPVerification.DoesNotExist:
            return Response(
                {'error': 'No OTP found. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            return Response(
                {'error': 'An error occurred. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ResetPasswordView(APIView):
    """Reset password using OTP"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0] if serializer.errors else 'Invalid data'
            return Response(
                {
                    'success': False,
                    'error': {'message': first_error}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']
        
        try:
            # Verify OTP again
            otp_record = OTPVerification.objects.filter(
                email=email,
                type='PASSWORD_RESET',
                is_used=False
            ).latest('created_at')
            
            # Double-check OTP is valid
            if otp_record.is_expired():
                return Response(
                    {'error': 'OTP has expired. Please request a new one.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify hash match
            if not OTPManager.verify_otp_hash(otp, otp_record.otp_hash):
                 return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get user
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                # Security: Don't reveal if user exists
                return Response(
                    {'message': 'If this email exists, password has been reset.'},
                    status=status.HTTP_200_OK
                )
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Mark OTP as used
            otp_record.mark_used()
            
            # Invalidate all other OTPs
            OTPVerification.objects.filter(
                email=email,
                is_used=False
            ).update(is_used=True)
            
            # Send confirmation email
            EmailService.send_password_reset_confirmation(email)
            
            logger.info(f"Password reset successfully for {email}")
            
            return Response(
                {
                    'success': True,
                    'message': 'Password reset successfully. Please login with your new password.'
                },
                status=status.HTTP_200_OK
            )
            
        except OTPVerification.DoesNotExist:
            return Response(
                {'error': 'OTP verification failed. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            return Response(
                {'error': 'An error occurred. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_profile(request):
    """
    PUT /api/accounts/profile/update/
    
    Update user profile.
    NOTE: Request must be multipart/form-data for image upload.
    """
    try:
        # 1. Update Profile via Service
        success, message = ProfileService.update_profile(request.user, request.data)
        
        if not success:
             return Response(
                {'success': False, 'message': message},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # 2. Get fresh profile data to return
        profile_data = ProfileService.get_profile(request.user)
        
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'data': profile_data
        })
        
    except Exception as e:
        logger.error(f"Profile update API error: {str(e)}")
        return Response(
            {'success': False, 'message': 'An error occurred while updating profile.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def colleges_list(request):
    """
    GET /api/accounts/colleges/
    List all active colleges.
    """
    from .models import College
    colleges = College.objects.filter(is_active=True).values('id', 'name', 'code')
    return Response({
        'success': True,
        'data': list(colleges)
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sessions(request):
     """
     GET /api/accounts/sessions/
     List active login sessions.
     """
     # Placeholder implementation
     return Response({'success': True, 'data': []})

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def request_password_reset_link(request):
    """
    POST /api/accounts/password-reset/request/
    Send reset link email (New System).
    """
    email = request.data.get('email')
    if not email:
        return Response({'success': False, 'message': 'Email is required'}, status=400)
        
    success, message = AuthService.request_password_reset_link(email)
    
    if success:
        return Response({'success': True, 'message': message})
    else:
        # Return 200 for security unless it's a server error, but message indicates success state
        return Response({'success': False, 'message': message}, status=400)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@parser_classes([FormParser, MultiPartParser])
def password_reset_confirm(request, token):
    """
    GET/POST /accounts/reset-password/<token>/
    Web View for resetting password.
    """
    from django.shortcuts import render
    
    # GET: Show Form
    if request.method == 'GET':
        valid, email, error = AuthService.verify_password_reset_token(token)
        if not valid:
            return render(request, 'auth/password_reset_invalid.html', {'error': error})
            
        return render(request, 'auth/password_reset_confirm.html', {'token': token})
        
    # POST: Process Form
    elif request.method == 'POST':
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if new_password != confirm_password:
             return render(request, 'auth/password_reset_confirm.html', {'error': "Passwords do not match", 'token': token})
             
        if len(new_password) < 8:
             return render(request, 'auth/password_reset_confirm.html', {'error': "Password must be at least 8 chars", 'token': token})

        success, msg = AuthService.complete_password_reset(token, new_password)
        
        if success:
            return render(request, 'auth/password_reset_done.html')
        else:
            return render(request, 'auth/password_reset_confirm.html', {'error': msg, 'token': token})
