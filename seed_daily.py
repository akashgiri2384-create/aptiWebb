
import os
import django
from django.utils import timezone
import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quizzy.settings")
django.setup()

from quizzes.models import Quiz, Category
from daily_quizzes.models import DailyQuiz

def seed_daily_quizzes():
    today = timezone.now().date()
    print(f"Seeding daily quizzes for {today}...")

    # Ensure we have a category
    category, _ = Category.objects.get_or_create(
        name="General", 
        defaults={'slug': 'general', 'description': 'General topics'}
    )

    # Ensure we have at least one quiz to link
    quiz, _ = Quiz.objects.get_or_create(
        title="Daily Morning Challenge",
        defaults={
            'description': "A quick morning brain warmup.",
            'category': category,
            'difficulty': 'easy',
            'duration_minutes': 5,
            'is_published': True
        }
    )

    # Create Morning Quiz
    DailyQuiz.objects.get_or_create(
        date=today,
        slot='morning',
        defaults={
            'quiz_title': "Morning Boost",
            'difficulty': 'easy',
            'keys_required': 1,
            'xp_multiplier': 1.5,
            'quiz': quiz
        }
    )

    # Create Evening Quiz
    DailyQuiz.objects.get_or_create(
        date=today,
        slot='evening',
        defaults={
            'quiz_title': "Evening Logic",
            'difficulty': 'medium',
            'keys_required': 2,
            'xp_multiplier': 2.0,
            'quiz': quiz
        }
    )

    # Create Night Quiz
    DailyQuiz.objects.get_or_create(
        date=today,
        slot='night',
        defaults={
            'quiz_title': "Night Owl Hardcore",
            'difficulty': 'hard',
            'keys_required': 3,
            'xp_multiplier': 3.0,
            'quiz': quiz
        }
    )

    print("Daily quizzes seeded successfully!")

if __name__ == '__main__':
    seed_daily_quizzes()
