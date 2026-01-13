"""
Quick test script to create sample data and verify models work.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizzy.settings')
django.setup()

from accounts.models import CustomUser, College, UserProfile
from quizzes.models import Category, Quiz, Question
from xp_system.models import XPConfig, UserStats

print("Testing Database Models...")

# Create college
college, _ = College.objects.get_or_create(
    code='TEST_COL',
    defaults={'name': 'Test College', 'city': 'Test City', 'state': 'Test State'}
)
print(f"[OK] College: {college.name}")

# Create user
user, created = CustomUser.objects.get_or_create(
    email='test@quizzy.com',
    defaults={
        'full_name': 'Test User',
        'college': college
    }
)
if created:
    user.set_password('testpass123')
    user.save()
print(f"[OK] User: {user.email}")

# Create user profile (auto-created via signals or manually)
profile, _ = UserProfile.objects.get_or_create(user=user)
print(f"[OK] UserProfile: Total XP = {profile.total_xp}")

# Create category
category, _ = Category.objects.get_or_create(
    name='Mathematics',
    defaults={'slug': 'mathematics', 'color': '#FF5733'}
)
print(f"[OK] Category: {category.name}")

# Create quiz
quiz, _ = Quiz.objects.get_or_create(
    title='Basic Math Quiz',
    defaults={
        'description': 'Test your basic math skills',
        'category': category,
        'difficulty': 'easy',
        'duration_minutes': 30,
    }
)
print(f"[OK] Quiz: {quiz.title}")

# Create questions
if quiz.questions.count() == 0:
    for i in range(1, 6):
        Question.objects.create(
            quiz=quiz,
            text=f"What is {i} + {i}?",
            option_a=str(i * 2),
            option_b=str(i * 3),
            option_c=str(i + 1),
            option_d=str(i - 1),
            correct_answer='A',
            sequence=i
        )
    print(f"[OK] Created 5 questions for {quiz.title}")
else:
    print(f"[OK] Quiz already has {quiz.questions.count()} questions")

# Create XP Config
config, _ = XPConfig.objects.get_or_create(
    pk=1,
    defaults={
        'xp_easy_correct': 10,
        'xp_medium_correct': 25,
        'xp_hard_correct': 50,
    }
)
print(f"[OK] XPConfig: Easy={config.xp_easy_correct} XP")

# Create UserStats
stats, _ = UserStats.objects.get_or_create(user=user)
print(f"[OK] UserStats: Level {stats.level}, {stats.total_xp} XP")

print("\nAll models working! Database is ready!")
print(f"\nSummary:")
print(f"   - Colleges: {College.objects.count()}")
print(f"   - Users: {CustomUser.objects.count()}")
print(f"   - Categories: {Category.objects.count()}")
print(f"   - Quizzes: {Quiz.objects.count()}")
print(f"   - Questions: {Question.objects.count()}")
print(f"\n[OK] Test user: test@quizzy.com / testpass123")
