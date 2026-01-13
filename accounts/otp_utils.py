import hashlib
import secrets
import os
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

class OTPManager:
    """Manage OTP generation, hashing, and verification"""
    
    OTP_LENGTH = int(os.getenv('OTP_LENGTH', 6))
    OTP_EXPIRY_MINUTES = int(os.getenv('OTP_EXPIRY_MINUTES', 5))
    OTP_MAX_ATTEMPTS = int(os.getenv('OTP_MAX_ATTEMPTS', 5))
    
    @staticmethod
    def generate_otp():
        """Generate a random 6-digit OTP"""
        return str(secrets.randbelow(10 ** OTPManager.OTP_LENGTH)).zfill(OTPManager.OTP_LENGTH)
    
    @staticmethod
    def hash_otp(otp):
        """Hash OTP using SHA-256"""
        return hashlib.sha256(otp.encode()).hexdigest()
    
    @staticmethod
    def verify_otp_hash(otp, otp_hash):
        """Verify OTP against stored hash"""
        return OTPManager.hash_otp(otp) == otp_hash
    
    @staticmethod
    def get_otp_expiry():
        """Get OTP expiry datetime"""
        return timezone.now() + timedelta(minutes=OTPManager.OTP_EXPIRY_MINUTES)
    
    @staticmethod
    def can_resend_otp(email, otp_type):
        """Check if user can resend OTP (cooldown check)"""
        from .models import OTPVerification
        
        cooldown = int(os.getenv('OTP_RESEND_COOLDOWN_SECONDS', 60))
        recent_otp = OTPVerification.objects.filter(
            email=email,
            type=otp_type,
            created_at__gte=timezone.now() - timedelta(seconds=cooldown)
        ).exists()
        
        return not recent_otp
