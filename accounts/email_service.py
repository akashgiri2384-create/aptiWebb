from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.core.mail import send_mail, get_connection
from decouple import config
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Send OTP emails via Gmail"""
    
    SENDER_NAME = "IQurio Security"
    # SENDER_EMAIL removed to force dynamic retrieval from settings
    
    @staticmethod
    def send_otp_email(email, otp, otp_type):
        """Send OTP email to user"""
        try:
            # Email context
            context = {
                'otp': otp,
                'otp_type': otp_type,
                'expiry_minutes': 5,
                'app_name': 'IQurio'
            }
            
            # Render HTML email
            html_message = render_to_string('emails/otp_email.html', context)
            plain_message = strip_tags(html_message)
            
            # Formatted subject
            subject_type = "Password Reset" if otp_type == 'PASSWORD_RESET' else "Verification"
            
            # Send email
            print(f"DEBUG: Attempting to send OTP from: {settings.DEFAULT_FROM_EMAIL}")
            send_mail(
                subject=f'{subject_type} OTP - IQurio',
                message=plain_message,
                from_email=f'{EmailService.SENDER_NAME} <{settings.DEFAULT_FROM_EMAIL}>',
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"OTP email sent to {email} for {otp_type}")
            return True, None
            
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                error_msg += f" | API Response: {e.response.text}"
            logger.error(f"Failed to send OTP email to {email}: {error_msg}")
            print(f"EMAIL ERROR: {error_msg}") # Print to console for user visibility
            return False, error_msg
    
    @staticmethod
    def send_password_reset_confirmation(email):
        """Send password reset success email"""
        try:
            subject = 'Password Changed Successfully - IQurio'
            message = 'Your password has been successfully reset. If you did not perform this action, please contact support immediately.'
            
            send_mail(
                subject=subject,
                message=message,
                from_email=f'{EmailService.SENDER_NAME} <{settings.DEFAULT_FROM_EMAIL}>',
                recipient_list=[email],
                fail_silently=False,
            )
            
            logger.info(f"Password reset confirmation email sent to {email}")
            return True, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send password reset email to {email}: {error_msg}")
            return False, error_msg
    @staticmethod
    def send_verification_link_email(user, token, request=None):
        """Send email verification link to user"""
        try:
            # Construct link
            if request:
                protocol = 'https' if request.is_secure() else 'http'
                domain = request.get_host()
                base_url = f"{protocol}::{domain}"
            else:
                base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

            verify_url = f"{base_url}/api/accounts/verify-email?token={token}"

            # Email context
            context = {
                'user': user,
                'verify_url': verify_url,
                'expiry_hours': 24,
                'app_name': 'IQurio'
            }
            
            html_message = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
                <h2 style="color: #4a90e2;">Verify your Email</h2>
                <p>Hi {user.full_name},</p>
                <p>Thank you for registering with {context['app_name']}. Please click the link below to verify your email address:</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}" style="background-color: #4a90e2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">Verify Email</a>
                </p>
                </p>
                <p>This link will expire in 24 hours.</p>
                <p>Best regards,<br>The Team</p>
            </div>
            """
            
            plain_message = strip_tags(html_message)
            
            # Use Default Backend (Brevo) - No Custom Connection needed
            send_mail(
                subject='Verify your Email - IQurio',
                message=plain_message,
                from_email=settings.VERIFICATION_FROM_EMAIL,  # <--- Changed this
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Verification email sent to {user.email}")
            return True, None
            
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                error_msg += f" | API Response: {e.response.text}"
            print(f"CRITICAL EMAIL ERROR: {error_msg}")
            logger.error(f"Failed to send verification email to {user.email}: {error_msg}")
            return False, error_msg

    @staticmethod
    def send_pre_verification_email(email, name, token, request=None):
        """Send pre-registration email verification link"""
        try:
            # Construct link
            if request:
                protocol = 'https' if request.is_secure() else 'http'
                domain = request.get_host()
                base_url = f"{protocol}::{domain}"
            else:
                base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

            verify_url = f"{base_url}/api/accounts/confirm-email?token={token}"

            context = {'app_name': 'IQurio'}
            
            html_message = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
                <h2 style="color: #4a90e2;">Verify your Email</h2>
                <p>Hi {name},</p>
                <p>Please verify your email address to continue registration with {context['app_name']}.</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}" style="background-color: #4a90e2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">Verify Email</a>
                </p>
                </p>
                <p>This link is valid for 10 minutes.</p>
            </div>
            """
            
            plain_message = strip_tags(html_message)
            
            # Use Default Backend (Brevo)
            send_mail(
                subject='Verify Email - IQurio',
                message=plain_message,
                from_email=settings.VERIFICATION_FROM_EMAIL, # <--- Changed this
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Pre-verification email sent to {email}")
            return True, None
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                error_msg += f" | API Response: {e.response.text}"
            logger.error(f"Failed to send pre-verification email to {email}: {error_msg}")
            return False, error_msg

    @staticmethod
    def send_password_reset_link(email, token):
        """Send password reset link"""
        try:
            base_url = settings.SITE_URL
            reset_url = f"{base_url}/accounts/reset-password/{token}/"

            html_message = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
                <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h2 style="color: #1a1a1a; margin-top: 0;">Password Reset Request</h2>
                    <p style="color: #4a4a4a; font-size: 16px;">Hello,</p>
                    <p style="color: #4a4a4a; font-size: 16px;">We received a request to reset your password for your IQurio account. If you didn't make this request, you can safely ignore this email.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="background: linear-gradient(135deg, #6366f1, #4f46e5); color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Reset Password</a>
                    </div>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px; text-align: center;">This link will expire in 15 minutes.</p>
                </div>
            </div>
            """
            
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject='Reset your Password - IQurio',
                message=plain_message,
                from_email=f'{EmailService.SENDER_NAME} <{settings.DEFAULT_FROM_EMAIL}>',
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Password reset link sent to {email}")
            return True, None
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                error_msg += f" | API Response: {e.response.text}"
            logger.error(f"Failed to send password reset link to {email}: {error_msg}")
            print(f"RESET LINK ERROR: {error_msg}")
            return False, error_msg
