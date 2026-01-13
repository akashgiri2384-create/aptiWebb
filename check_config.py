import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizzy.settings')
django.setup()

def check_settings():
    print("--- DJANGO EMAIL CONFIG ---")
    print(f"EMAIL_HOST_USER: '{settings.EMAIL_HOST_USER}'")
    print(f"DEFAULT_FROM_EMAIL: '{settings.DEFAULT_FROM_EMAIL}'")
    print(f"SERVER_EMAIL: '{settings.SERVER_EMAIL}'")
    
    # Check .env directly via decouple if possible, matching settings.py logic
    from decouple import config
    print("\n--- DECOUPLE RAW CONFIG ---")
    try:
        print(f"EMAIL_HOST_USER: '{config('EMAIL_HOST_USER')}'")
    except:
        print("EMAIL_HOST_USER: Not found in .env")

if __name__ == "__main__":
    check_settings()
