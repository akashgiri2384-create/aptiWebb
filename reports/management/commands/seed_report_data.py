from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import College
from quizzes.models import Quiz, QuizAttempt
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds demo data for Report Testing (10 Branches)'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding Demo Report Data...")
        
        # 1. Setup College
        college, _ = College.objects.get_or_create(name="Indira University", defaults={'code': 'IU001'})
        
        # 2. Branches
        branches = [
            'Computer Science', 'Information Technology', 'Civil Engineering', 
            'Mechanical Engineering', 'Electrical Engineering', 'Electronics',
            'Data Science', 'AI & ML', 'Cyber Security', 'Bio-Technology'
        ]
        
        # 3. Ensure a Dummy Quiz exists for attempts
        from quizzes.models import Category
        category, _ = Category.objects.get_or_create(name="General Aptitude")
        
        quiz, _ = Quiz.objects.get_or_create(
            title="Aptitude Mock Test 1", 
            defaults={'category': category, 'duration_minutes': 30, 'difficulty': 'medium'}
        )
        
        # 4. Create Students and Attempts
        for i, branch in enumerate(branches):
            # Create 3 students per branch
            for j in range(1, 4):
                email = f"student_{i}_{j}@demo.com"
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'full_name': f"Student {branch[:3]} {j}",
                        'branch': branch,
                        'college': college,
                        'roll_number': f"{branch[:2].upper()}-25-{j:03d}",
                        'year': 2
                    }
                )
                
                if created:
                    user.set_password('pass123')
                    user.save()
                    
                # Create detailed Attempt
                score = random.randint(30, 95)
                status = 'graded'
                
                QuizAttempt.objects.create(
                    user=user,
                    quiz=quiz,
                    status=status,
                    submitted_at=timezone.now() - timedelta(days=random.randint(0, 5)),
                    total_questions=20,
                    correct_count=int(20 * (score/100)),
                    wrong_count=20 - int(20 * (score/100)),
                    percentage_score=score
                )
                
        self.stdout.write(self.style.SUCCESS(f"Successfully created ~30 students across 10 branches in {college.name}."))
