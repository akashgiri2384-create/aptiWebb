
import os
import django
import sys

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizzy.settings')
django.setup()

from quizzes.models import Category, Quiz, Question
from django.utils import timezone

def populate():
    print(">> Starting population script...")

    # 1. Ensure Category
    cat, created = Category.objects.get_or_create(
        slug='daily-challenge',
        defaults={
            'name': 'Daily Challenge',
            'description': 'Test your skills with daily aptitude challenges.',
            'color': '#F59E0B',
            'icon': 'fas fa-fire',
            'emoji': '🔥'
        }
    )
    if created:
        print(f">> Created Category: {cat.name}")
    else:
        print(f">> Category exists: {cat.name}")

    # 2. Create 3 Quizzes
    quiz_titles = [
        "Daily Aptitude Mix 01",
        "Daily Logic Puzzle 02",
        "Daily Verbal Ability 03"
    ]

    for i, title in enumerate(quiz_titles):
        quiz, created = Quiz.objects.get_or_create(
            title=title,
            category=cat,
            defaults={
                'description': f"Daily challenge for {timezone.now().strftime('%B %d')}. test your speed!",
                'difficulty': 'medium',
                'duration_minutes': 10,
                'passing_percentage': 50,
                'xp_per_correct': 20,
                'is_published': True,
                'is_active': True
            }
        )
        if created:
            print(f">> Created Quiz: {quiz.title}")
        
        # 3. Add/Reset Questions
        # Force Clean existing questions to ensure data integrity
        if quiz.questions.exists():
            print(f"   - Cleaning {quiz.questions.count()} existing questions for {quiz.title}")
            quiz.questions.all().delete()

        questions_data = [
            {
                "text": "What is 15% of 200?",
                "options": ["20", "25", "30", "35"],
                "correct": "C"
            },
            {
                "text": "Find the next number: 5, 10, 15, ?",
                "options": ["20", "24", "30", "32"],
                "correct": "A"
            },
            {
                "text": "Synonym of 'Happy' is:",
                "options": ["Sad", "Joyful", "Angry", "Bored"],
                "correct": "B"
            },
            {
                "text": "If A is brother of B, and B is sister of C, how is A related to C?",
                "options": ["Brother", "Sister", "Cousin", "Father"],
                "correct": "A"
            },
            {
                "text": "Speed = Distance / ?",
                "options": ["Time", "Mass", "Force", "Volume"],
                "correct": "A"
            }
        ]

        for idx, q_data in enumerate(questions_data):
            Question.objects.create(
                quiz=quiz,
                text=q_data['text'],
                explanation="Basic aptitude concept.",
                option_a=q_data['options'][0],
                option_b=q_data['options'][1],
                option_c=q_data['options'][2],
                option_d=q_data['options'][3],
                correct_answer=q_data['correct'],
                sequence=idx + 1
            )
        print(f"   >> Added 5 Questions to {quiz.title}")

    print(">> Population Complete!")

if __name__ == '__main__':
    populate()
