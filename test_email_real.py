
import os
import sys
import django
from django.conf import settings
from django.core.mail import send_mail, get_connection
from decouple import config

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizzy.settings')
django.setup()

def test_email():
    print("--- STARTING EMAIL TEST ---")
    
    # 1. Test Standard Email (if configured)
    user = config('EMAIL_HOST_USER', default='')
    password = config('EMAIL_HOST_PASSWORD', default='')
    print(f"Standard Email: {user}")
    
    if user and password:
        try:
            print("Attempting Standard Send...")
            send_mail(
                'Test Email Standard',
                'This is a test.',
                user,
                [user], # Send to self
                fail_silently=False,
            )
            print("Standard: SUCCESS")
        except Exception as e:
            print(f"Standard: FAILED - {e}")
    else:
        print("Standard: SKIPPED (Missing credentials)")

    # 2. Test Verification Email (The one failing)
    v_user = config('VERIFICATION_EMAIL_HOST_USER', default='')
    v_pass = config('VERIFICATION_EMAIL_HOST_PASSWORD', default='')
    
    print(f"\nVerification Email: {v_user}")
    print(f"Verification Pass: '{v_pass}' (Len: {len(v_pass)})")
    
    if v_user and v_pass:
        try:
            # Replicating logic from email_service.py
            connection = get_connection(
                backend=settings.EMAIL_BACKEND,
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=v_user,
                password=v_pass,
                use_tls=settings.EMAIL_USE_TLS
            )
            
            print(f"Attempting Verification Send (Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT} TLS:{settings.EMAIL_USE_TLS})...")
            
            send_mail(
                'Test Email Verification',
                'This is a verification test.',
                f'Verify <{v_user}>',
                [v_user], # Send to self
                fail_silently=False,
                connection=connection
            )
            print("Verification: SUCCESS")
        except Exception as e:
            print(f"Verification: FAILED - {e}")
    else:
        print("Verification: SKIPPED (Missing credentials)")

if __name__ == "__main__":
    test_email()
