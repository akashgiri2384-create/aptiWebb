import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizzy.settings')
django.setup()

from daily_quizzes.models import DailyQuiz
from quizzes.models import Quiz, Category

def create_quizzes():
    today = timezone.now().date()
    
    # 1. Ensure Category
    cat, _ = Category.objects.get_or_create(name="Daily Challenge", defaults={'slug': 'daily-challenge'})
    
    # 2. Create 3 Quizzes
    quizzes = []
    titles = ["Morning Brain Teaser", "Evening Logic Puzzle", "Night Owl Trivia"]
    
    for title in titles:
        q, created = Quiz.objects.get_or_create(
            title=title,
            defaults={
                'category': cat,
                'description': f"Daily challenge for {today}",
                'duration_minutes': 5,
                'difficulty': 'medium',
                'is_published': True
            }
        )
        quizzes.append(q)
        print(f"Quiz '{q.title}' ready.")

    # 3. Create Daily Quizzes
    slots = ['morning', 'evening', 'night']
    keys = [5, 5, 5]
    
    for i, slot in enumerate(slots):
        dq, created = DailyQuiz.objects.update_or_create(
            date=today,
            slot=slot,
            defaults={
                'quiz': quizzes[i],
                'quiz_title': quizzes[i].title,
                'keys_required': keys[i],
                'is_active': True,
                'difficulty': 'medium'
            }
        )
        print(f"DailyQuiz for {slot} created.")

if __name__ == "__main__":
    create_quizzes()
