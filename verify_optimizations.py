
import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizzy.settings")
django.setup()

from quizzes.services import QuizService
from django.contrib.auth import get_user_model

User = get_user_model()

def verify_quiz_list():
    print("Verifying get_quizzes_list...")
    
    # Test anonymous
    print("Testing anonymous user...")
    try:
        data = QuizService.get_quizzes_list(limit=5)
        print(f"Success! Retrieved {len(data['results'])} quizzes.")
    except Exception as e:
        print(f"FAILED (Anonymous): {e}")
        import traceback
        traceback.print_exc()

    # Test authenticated (if any user exists)
    user = User.objects.first()
    if user:
        print(f"Testing with user: {user.email}")
        try:
            data = QuizService.get_quizzes_list(user=user, limit=5)
            print(f"Success! Retrieved {len(data['results'])} quizzes with user data.")
            if data['results']:
                print("Sample Data:", data['results'][0].get('best_score'))
        except Exception as e:
            print(f"FAILED (Authenticated): {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No users found to test authenticated flow.")

if __name__ == "__main__":
    verify_quiz_list()
