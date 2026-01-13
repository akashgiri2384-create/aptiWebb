"""
Business logic services for accounts app.

Services:
- AuthService: Authentication and user management
- ProfileService: User profile operations
- SessionService: Session management
"""

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import logging
import uuid
import secrets
from django.conf import settings

from .models import CustomUser, UserProfile, College, LoginSession, PasswordReset, EmailVerificationToken, PreRegistrationVerification
from .email_service import EmailService

logger = logging.getLogger('quizzy')


class AuthService:
    """Core authentication business logic."""
    
    @staticmethod
    @transaction.atomic
    @staticmethod
    @transaction.atomic
    def register_user(email, password, full_name, college, **kwargs):
        """
        Register a new user with validation.
        
        Args:
            email: User email address
            password: User password
            full_name: User's full name
            college: College object
            **kwargs: Additional user fields
            
        Returns:
            tuple: (success: bool, data/message: dict/str)
        """
        # Validation
        if CustomUser.objects.filter(email=email).exists():
            return False, "Email already registered"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."
        
        if len(full_name.strip()) < 2:
            return False, "Full Name is required."
            
        # Check Duplicate Email
        if CustomUser.objects.filter(email=email).exists():
            return False, "An account with this email already exists. Please login."
            
        # Check Duplicate Mobile
        mobile_number = kwargs.get('mobile_number')
        if mobile_number and CustomUser.objects.filter(mobile_number=mobile_number).exists():
            return False, "This mobile number is already registered with another account."
        
        # Validate college
        if not college or not college.is_active:
             return False, "Please select a valid college."
             
        # Validate other academic fields
        if not kwargs.get('year'):
            return False, "Please select your Year."
        if not kwargs.get('branch'):
            return False, "Please select your Branch."
        
        # Check if terms accepted
        if not kwargs.get('accepted_terms', False):
            return False, "You must accept the terms and conditions."
        
        if not kwargs.get('accepted_privacy', False):
            return False, "You must accept the privacy policy."
            
        # Check Pre-Registration Verification
        if not AuthService.check_verification_status(email):
            return False, "Please verify your email address before registering."
        
        try:
            # Create user
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                full_name=full_name.strip(),
                college=college,
                year=kwargs.get('year'),
                branch=kwargs.get('branch'),
                roll_number=kwargs.get('roll_number'),
                mobile_number=mobile_number,
                accepted_terms=True,
                accepted_terms_at=timezone.now(),
                accepted_privacy=True,
                accepted_privacy_at=timezone.now(),
                is_email_verified=True # Pre-verified
            )
            
            # Create profile
            UserProfile.objects.create(user=user)
            
            logger.info(f"User registered successfully: {email}")
            
            return True, {
                'user_id': str(user.id),
                'email': user.email,
                'full_name': user.full_name,
                'message': 'Account created successfully.'
            }
        
        except Exception as e:
            logger.error(f"Registration error for {email}: {str(e)}")
            return False, "Registration failed. Please try again."
            return False, "Registration failed. Please try again."

    @staticmethod
    @transaction.atomic
    def verify_email_token(token):
        """Verify email using token"""
        try:
            verification = EmailVerificationToken.objects.select_related('user').get(
                token=token,
                is_used=False,
                expires_at__gt=timezone.now()
            )
            
            user = verification.user
            user.is_email_verified = True
            user.save()
            
            # Mark token as used
            verification.is_used = True
            verification.save()
            
            logger.info(f"Email verified for user {user.email}")
            return True, "Email verified successfully"
            
        except EmailVerificationToken.DoesNotExist:
            return False, "Invalid or expired verification link"
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            return False, "Verification failed"
    
            logger.error(f"Email verification error: {str(e)}")
            return False, "Verification failed"

    @staticmethod
    def initiate_email_verification(email, name):
        """Start pre-registration verification"""
        # Check if email already used by existing user
        if CustomUser.objects.filter(email=email).exists():
            return False, "Email already registered. Please login."
            
        token = secrets.token_urlsafe(32)
        # Create or update verification record
        PreRegistrationVerification.objects.update_or_create(
            email=email,
            defaults={
                'token': token,
                'is_verified': False,
                'expires_at': timezone.now() + timedelta(minutes=10)
            }
        )
        
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        if settings.DEBUG:
            print(f"\n{'='*60}")
            print(f" [DEBUG] 📧 CLICK THIS LINK TO VERIFY EMAIL:")
            print(f" {base_url}/api/accounts/confirm-email?token={token}")
            print(f"{'='*60}\n")

        success, error = EmailService.send_pre_verification_email(email, name, token)
        if success:
            return True, "Verification link sent."
        else:
            return False, f"Failed to send verification email: {error}"

    @staticmethod
    def confirm_email_token(token):
        """Confirm the pre-registration token"""
        try:
            record = PreRegistrationVerification.objects.get(
                token=token,
                expires_at__gt=timezone.now()
            )
            record.is_verified = True
            record.save()
            return True, "Email verified successfully.", record.email
        except PreRegistrationVerification.DoesNotExist:
            return False, "Invalid or expired link.", None

    @staticmethod
    def check_verification_status(email):
        """Check if email is verified"""
        try:
            record = PreRegistrationVerification.objects.filter(
                email=email, 
                is_verified=True,
                expires_at__gt=timezone.now()
            ).first() # Use filter.first() to avoid multiple objects error if duplicates exist (though update_or_create handles it)
            return record is not None
        except:
            return False

    @staticmethod
    def login_user(email, password, request):
        """
        Authenticate user and return JWT tokens.
        
        Args:
            email: User email
            password: User password
            request: HTTP request object
            
        Returns:
            tuple: (success: bool, data/message: dict/str, message: str)
        """
        # Authenticate
        user = authenticate(username=email, password=password)
        
        if not user:
            logger.warning(f"Failed login attempt for: {email}")
            return False, None, "Invalid email or password"
        
        # Check account status
        if user.is_banned:
            logger.warning(f"Banned user login attempt: {email}")
            return False, None, f"Account banned: {user.ban_reason}"
        
        if not user.is_active:
            logger.warning(f"Inactive user login attempt: {email}")
            return False, None, "Account is inactive"
        
        # Update login info
        user.last_login_at = timezone.now()
        user.login_count += 1
        user.save(update_fields=['last_login_at', 'login_count'])
        
        # Create login session
        ip = AuthService.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        device_type = AuthService.detect_device_type(user_agent)
        
        # Establish Django Session (Cookie) for Web Views
        from django.contrib.auth import login
        login(request, user)
        
        LoginSession.objects.create(
            user=user,
            ip_address=ip,
            user_agent=user_agent,
            device_type=device_type
        )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        logger.info(f"User logged in successfully: {email} from {ip}")
        
        return True, {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': str(user.id),
                'email': user.email,
                'full_name': user.full_name,
                'college': user.college.name if user.college else None,
                'user_type': user.user_type,
            }
        }, "Login successful"
    
    @staticmethod
    def logout_user(user):
        """
        Mark current session as inactive.
        
        Args:
            user: CustomUser instance
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Find active session
            session = LoginSession.objects.filter(
                user=user,
                is_active=True
            ).order_by('-login_at').first()
            
            if session:
                session.logout_at = timezone.now()
                session.is_active = False
                session.save(update_fields=['logout_at', 'is_active'])
            
            logger.info(f"User logged out: {user.email}")
            return True, "Logout successful"
        
        except Exception as e:
            logger.error(f"Logout error for {user.email}: {str(e)}")
            return False, "Logout failed"
    
    @staticmethod
    def change_password(user, old_password, new_password):
        """
        Change user password with validation.
        
        Args:
            user: CustomUser instance
            old_password: Current password
            new_password: New password
            
        Returns:
            tuple: (success: bool, message: str)
        """
        # Validate old password
        if not user.check_password(old_password):
            logger.warning(f"Incorrect old password for: {user.email}")
            return False, "Current password is incorrect"
        
        # Validate new password
        if len(new_password) < 8:
            return False, "New password must be at least 8 characters"
        
        if old_password == new_password:
            return False, "New password must be different from current password"
        
        try:
            # Set new password
            user.set_password(new_password)
            user.save(update_fields=['password'])
            
            # Invalidate all active sessions except current
            LoginSession.objects.filter(
                user=user,
                is_active=True
            ).update(
                is_active=False,
                logout_at=timezone.now()
            )
            
            logger.info(f"Password changed for: {user.email}")
            return True, "Password changed successfully"
        
        except Exception as e:
            logger.error(f"Password change error for {user.email}: {str(e)}")
            return False, "Password change failed"
    
    @staticmethod
    def get_client_ip(request):
        """
        Extract client IP address from request.
        
        Args:
            request: HTTP request object
            
        Returns:
            str: Client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip
    
    @staticmethod
    def detect_device_type(user_agent):
        """
        Detect device type from user agent string.
        
        Args:
            user_agent: User agent string
            
        Returns:
            str: Device type (mobile/tablet/desktop/unknown)
        """
        user_agent_lower = user_agent.lower()
        
        if 'mobile' in user_agent_lower or 'android' in user_agent_lower:
            return 'mobile'
        elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            return 'tablet'
        elif 'windows' in user_agent_lower or 'mac' in user_agent_lower or 'linux' in user_agent_lower:
            return 'desktop'
        else:
            return 'unknown'
    
    @staticmethod
    def generate_password_reset_token(user):
        """
        Generate password reset token for user.
        
        Args:
            user: CustomUser instance
            
        Returns:
            PasswordReset instance
        """
        token = str(uuid.uuid4())
        expires_at = timezone.now() + timedelta(hours=24)
        
        password_reset = PasswordReset.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        
        logger.info(f"Password reset token generated for: {user.email}")
        return password_reset

    @staticmethod
    def request_password_reset_link(email):
        """
        Initiate password reset via link logic.
        """
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            # Security: Return true even if user not found to prevent enumeration
            return True, "If an account exists, a password reset link has been sent."
            
        try:
            # Invalidate existing tokens
            PasswordReset.objects.filter(user=user, is_used=False).update(is_used=True)
            
            # Generate new token
            reset_obj = AuthService.generate_password_reset_token(user)
            
            # Send Email
            success, error = EmailService.send_password_reset_link(user.email, reset_obj.token)
            if success:
                return True, "Password reset link sent to your email."
            else:
                return False, f"Failed to send email: {error}"
                
        except Exception as e:
            logger.error(f"Error requesting password reset link for {email}: {str(e)}")
            return False, "An error occurred. Please try again."

    @staticmethod
    def verify_password_reset_token(token):
        """
        Verify if a reset token is valid.
        Returns: (is_valid, user_email, error_message)
        """
        try:
            reset_obj = PasswordReset.objects.get(token=token, is_used=False)
            
            if reset_obj.is_expired():
                return False, None, "Link has expired."
                
            return True, reset_obj.user.email, None
            
        except PasswordReset.DoesNotExist:
            return False, None, "Invalid or used link."

    @staticmethod
    def complete_password_reset(token, new_password):
        """
        reset password using token
        """
        try:
            reset_obj = PasswordReset.objects.get(token=token, is_used=False)
            
            if reset_obj.is_expired():
                return False, "Link has expired."
            
            user = reset_obj.user
            user.set_password(new_password)
            user.save()
            
            # Mark Used
            reset_obj.is_used = True
            reset_obj.used_at = timezone.now()
            reset_obj.save()
            
            # Invalidate all sessions
            LoginSession.objects.filter(user=user, is_active=True).update(is_active=False)
            
            # Send Confirmation (Fire and forget, but good to know if it fails)
            EmailService.send_password_reset_confirmation(user.email)
            
            return True, "Password changed successfully."
            
        except PasswordReset.DoesNotExist:
             return False, "Invalid link."
        except Exception as e:
            logger.error(f"Reset complete error: {str(e)}")
            return False, "Failed to reset password."


class ProfileService:
    """User profile management service."""
    
    @staticmethod
    def get_profile(user):
        """
        Get user profile data.
        
        Args:
            user: CustomUser instance
            
        Returns:
            dict: User and profile data
        """
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            # Create profile if doesn't exist
            profile = UserProfile.objects.create(user=user)
        
        # Get level safely
        try:
            level = user.xp_stats.level
        except Exception:
            level = 1

        # Get Season XP safely
        try:
            season_xp = user.xp_stats.season_xp
        except Exception:
            season_xp = 0

        # Get Rank Badge
        rank_badge_data = None
        try:
            from xp_system.models import UserBadge
            ub = UserBadge.objects.filter(
                user=user,
                badge__rarity='rank'
            ).order_by('-badge__rank_order').first()
            
            if ub:
                rank_badge_data = {
                    'name': ub.badge.name,
                    'image': ub.badge.image_path,
                    'rank_order': ub.badge.rank_order
                }
        except Exception:
            pass

        return {
            'user': {
                'id': str(user.id),
                'email': user.email,
                'full_name': user.full_name,
                'mobile_number': user.mobile_number,
                'college': user.college.name if user.college else None,
                'college_id': str(user.college.id) if user.college else None,
                'year': user.year,
                'branch': user.branch,
                'roll_number': user.roll_number,
                'user_type': user.user_type,
                'is_email_verified': user.is_email_verified,
                'is_mobile_verified': user.is_mobile_verified,
                'created_at': user.created_at.isoformat(),
                'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None,
                'login_count': user.login_count,
            },
            'profile': {
                'avatar': profile.avatar if profile.avatar else None,
                'bio': profile.bio,
                'theme': profile.theme,
                'email_notifications': profile.email_notifications,
                'push_notifications': profile.push_notifications,
                'total_quizzes_attempted': profile.total_quizzes_attempted,
                'total_xp': profile.total_xp,
                'season_xp': season_xp,
                'level': level,
                'current_rank': profile.current_rank,
                'rank_badge': rank_badge_data,
                'accuracy_percentage': profile.accuracy_percentage,
                'practice_streak': profile.practice_streak,
                'total_keys': profile.total_keys,
            }
        }
    
    @staticmethod
    def update_profile(user, data):
        """
        Update user profile.
        
        Args:
            user: CustomUser instance
            data: Dict of fields to update
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Update user fields
            user_fields = ['full_name', 'mobile_number', 'year', 'branch', 'roll_number']
            user_updated = False
            
            for field in user_fields:
                if field in data:
                    setattr(user, field, data[field])
                    user_updated = True
            
            # Update college if provided
            if 'college_id' in data and data['college_id']:
                try:
                    college = College.objects.get(id=data['college_id'])
                    user.college = college
                    user_updated = True
                except College.DoesNotExist:
                    pass
            
            if user_updated:
                user.save()
            
            # Update profile fields
            try:
                profile = user.profile
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=user)
            
            profile_fields = ['bio', 'theme', 'email_notifications', 'push_notifications']
            profile_updated = False
            
            for field in profile_fields:
                if field in data:
                    setattr(profile, field, data[field])
                    profile_updated = True
            
            # Handle avatar upload
            if 'avatar' in data and data['avatar']:
                avatar_data = data['avatar']
                
                # Check if it's a file object (not string/url)
                if hasattr(avatar_data, 'read'):
                    from django.core.files.storage import default_storage
                    from django.core.files.base import ContentFile
                    import os
                    
                    # Generate filename
                    ext = os.path.splitext(avatar_data.name)[1]
                    filename = f"avatars/{user.id}_{uuid.uuid4().hex[:8]}{ext}"
                    
                    # Save file
                    saved_path = default_storage.save(filename, ContentFile(avatar_data.read()))
                    profile.avatar = default_storage.url(saved_path)
                else:
                    # Assume it's a URL string
                    profile.avatar = avatar_data
                    
                profile_updated = True
            
            if profile_updated:
                profile.save()
            
            # Invalidate dashboard cache
            try:
                from dashboard.services import DashboardService
                DashboardService.invalidate_cache(user)
            except ImportError:
                pass
            
            logger.info(f"Profile updated for: {user.email}")
            return True, "Profile updated successfully"
        
        except Exception as e:
            logger.error(f"Profile update error for {user.email}: {str(e)}")
            return False, "Profile update failed"


class SessionService:
    """Login session management service."""
    
    @staticmethod
    def get_active_sessions(user):
        """
        Get all active sessions for user.
        
        Args:
            user: CustomUser instance
            
        Returns:
            QuerySet: Active LoginSession objects
        """
        return LoginSession.objects.filter(
            user=user,
            is_active=True
        ).order_by('-login_at')
    
    @staticmethod
    def terminate_session(session_id, user):
        """
        Terminate a specific session.
        
        Args:
            session_id: UUID of session
            user: CustomUser instance (for security)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            session = LoginSession.objects.get(
                id=session_id,
                user=user,
                is_active=True
            )
            
            session.logout_at = timezone.now()
            session.is_active = False
            session.save(update_fields=['logout_at', 'is_active'])
            
            logger.info(f"Session terminated: {session_id} for {user.email}")
            return True, "Session terminated successfully"
        
        except LoginSession.DoesNotExist:
            return False, "Session not found"
        except Exception as e:
            logger.error(f"Session termination error: {str(e)}")
            return False, "Failed to terminate session"
