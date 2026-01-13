import os
import django
from django.conf import settings
from django.core.mail import send_mail

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizzy.settings')
django.setup()

def test_email():
    print("--- Testing Email Configuration ---")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    # Check for API Key if using Anymail
    if 'anymail' in settings.EMAIL_BACKEND:
        try:
            from anymail.message import AnymailMessage
            print("Anymail module found.")
            api_key = settings.ANYMAIL.get('BREVO_API_KEY', '')
            if api_key:
                print(f"BREVO_API_KEY found: {api_key[:5]}...{api_key[-5:]}")
            else:
                print("ERROR: BREVO_API_KEY is missing or empty in settings!")
        except ImportError:
            print("ERROR: django-anymail is not installed!")
            return

    try:
        print("\nAttempting to send test email...")
        send_mail(
            subject='Test Email from Local Debug',
            message='If you see this, Brevo Anymail is working locally.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['iqreports909@gmail.com'], # Sending to self/sender to test
            fail_silently=False,
        )
        print("SUCCESS: Email sent successfully!")
    except Exception as e:
        print(f"\nFAILURE: Could not send email.")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        
        # Check for specific Anymail errors
        if hasattr(e, 'response'):
             print(f"API Response: {e.response.text}")

if __name__ == '__main__':
    test_email()
