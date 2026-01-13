
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from xp_system.models import UserStats, Badge, UserBadge
from quizzes.models import Quiz, Category, Question, QuizAttempt, Answer
from quizzes.services import QuizService
from xp_system.services import XPService

User = get_user_model()

class Command(BaseCommand):
    help = 'Simulates Full Quiz Flow -> Rank Up -> Result Fetch'

    def handle(self, *args, **kwargs):
        # 1. Setup User
        email = "sim_quiz_user@example.com"
        User.objects.filter(email=email).delete() 
        user = User.objects.create_user(email=email, password="password123")
        stats = UserStats.objects.create(user=user)
        
        # Set XP just below Tome I (Rank 16)
        # Rank 16 threshold = 16^2 * 100 = 25600.
        target_xp = 25600
        stats.total_xp = target_xp - 100 # 100 XP short
        stats.season_xp = target_xp - 100
        stats.save()
        
        self.stdout.write(f"User Setup: XP={stats.total_xp}. Target={target_xp} (Tome I)")

        # 2. Setup Quiz
        category, _ = Category.objects.get_or_create(name="TestCat", slug="test-cat")
        quiz = Quiz.objects.create(
            title="Rank Up Quiz",
            category=category,
            duration_minutes=10,
            passing_percentage=50,
            is_published=True,
            is_active=True,
            xp_per_correct=200 # Enough to level up
        )
        q1 = Question.objects.create(quiz=quiz, text="Q1", option_a="A", option_b="B", correct_answer="A", is_active=True, sequence=1)
        
        self.stdout.write("Quiz Setup Complete.")

        # 3. Start Quiz
        success, start_data, err = QuizService.start_quiz(user, quiz.id)
        if not success:
            self.stdout.write(self.style.ERROR(f"Start Failed: {err}"))
            return
        attempt_id = start_data['attempt_id']
        self.stdout.write(f"Quiz Started: {attempt_id}")

        # 4. Answer Correctly
        QuizService.save_answer(attempt_id, q1.id, "A")

        # 5. Submit Quiz (Triggers XP -> Rank Up)
        self.stdout.write("Submitting Quiz...")
        success, submit_data, err = QuizService.submit_quiz(attempt_id)
        if not success:
             self.stdout.write(self.style.ERROR(f"Submit Failed: {err}"))
             return
        
        self.stdout.write(f"Quiz Submitted. XP Earned: {submit_data['xp']['total']}")

        # 6. Fetch Results (The API Call)
        self.stdout.write("Fetching Results API...")
        success, result_data, err = QuizService.get_quiz_results(attempt_id, user)
        
        if success:
            anim = result_data.get('rank_up_animation')
            if anim:
                self.stdout.write(self.style.SUCCESS("API RETURNED ANIMATION DATA!"))
                self.stdout.write(f"Video: {anim.get('video_path')}")
                if "tome" in anim.get('video_path', '').lower():
                     self.stdout.write(self.style.SUCCESS("CORRECT: Tome I Video."))
                else:
                     self.stdout.write(self.style.ERROR(f"WRONG VIDEO: {anim.get('video_path')}"))
            else:
                self.stdout.write(self.style.ERROR("API RETURNED NO ANIMATION DATA."))
                # Debug: Check logs
                from dashboard.models import UserActivityLog
                logs = UserActivityLog.objects.filter(user=user).order_by('-created_at')
                self.stdout.write("Recent Logs:")
                for l in logs[:3]:
                    self.stdout.write(f"- {l.activity_type}: {l.description} (meta: {l.metadata})")
        else:
            self.stdout.write(self.style.ERROR(f"Fetch Results Failed: {err}"))
