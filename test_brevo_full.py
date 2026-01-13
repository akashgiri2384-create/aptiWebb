import os
import django
from django.conf import settings
from django.core.mail import send_mail

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizzy.settings')
django.setup()

def test_start():
    print(f"\n--- TESTING BREVO EMAIL IDENTITIES ---")
    print(f"API KEY: {settings.ANYMAIL['BREVO_API_KEY'][:10]}...")

    identities = [
        ("OTP/Reset", settings.DEFAULT_FROM_EMAIL),
        ("Verification", settings.VERIFICATION_FROM_EMAIL),
        ("Reports", settings.REPORT_FROM_EMAIL)
    ]

    for label, sender in identities:
        print(f"\nTesting: {label} ({sender})")
        try:
            count = send_mail(
                subject=f"Test from {label}",
                message=f"This is a test email from {sender}.",
                from_email=sender,
                recipient_list=[settings.DEFAULT_FROM_EMAIL], # Send to main email
                fail_silently=False
            )

            if count == 1:
                print(f"[PASS] SUCCESS: {label} Accepted by API.")
            else:
                print(f"[FAIL] FAILURE: {label} Sent but count is 0.")
        except Exception as e:
            print(f"[FAIL] ERROR: {label} Failed.")
            print(str(e))
            if hasattr(e, 'response'):
                print(f"Response: {e.response.text if e.response else 'No Response'}")


if __name__ == "__main__":
    test_start()
