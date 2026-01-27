
import os
import django
import sys

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizzy.settings')
django.setup()

# Ensure we can print unicode characters (Fix for Windows console)
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from quizzes.models import Question

def check():
    print("Checking Questions...")
    questions = Question.objects.all()
    for q in questions:
        print(f"Q: {q.text}")
        print(f"   A: '{q.option_a}'")
        print(f"   B: '{q.option_b}'")
        print(f"   C: '{q.option_c}'")
        print(f"   D: '{q.option_d}'")
        if not q.option_a:
            print("   ⚠️  WARNING: Option A is empty!")

if __name__ == '__main__':
    try:
        check()
    except Exception as e:
        print(f"Error: {e}")
