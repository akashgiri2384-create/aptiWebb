"""
Business logic services for quizzes app.

Services:
- QuizService: Core quiz functionality (browse, start, submit, results)
- QuestionService: Question management
"""

from django.db.models import Avg, F, Count, Sum, Q, Prefetch
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from datetime import timedelta
import logging

from .models import Category, Quiz, Question, QuizAttempt, Answer

logger = logging.getLogger('quizzy')


class QuizService:
    """Quiz business logic implementation"""
    
    CACHE_TTL = 3600  # 1 hour
    
    @staticmethod
    def get_quizzes_list(category=None, difficulty=None, user=None, limit=20, offset=0):
        """
        Get filtered list of quizzes with caching.
        """
        # 1. Try to get base list from cache
        cache_key = f'quizzes_list:{category}:{difficulty}:{limit}:{offset}'
        
        # Helper function to build base list
        def build_quiz_list():
            quizzes_qs = Quiz.objects.filter(
                is_published=True,
                is_active=True
            ).select_related('category').annotate(
                active_question_count=Count('questions', filter=Q(questions__is_active=True))
            )
            
            # Exclude Daily Challenges from general practice (unless explicit)
            if category != 'daily-challenge':
                quizzes_qs = quizzes_qs.exclude(category__slug='daily-challenge')
                
                # Handle Daily Quiz Archival
                from datetime import date
                today_local = timezone.localtime(timezone.now()).date()
                feature_start_date = date(2026, 1, 24) # Cutoff for auto-archival
                
                quizzes_qs = quizzes_qs.exclude(
                    Q(daily_assignments__date__lt=feature_start_date) | 
                    Q(daily_assignments__date__gte=today_local)
                )
            
            if category:
                quizzes_qs = quizzes_qs.filter(category__slug=category)
            if difficulty:
                quizzes_qs = quizzes_qs.filter(difficulty=difficulty)
                
            total = quizzes_qs.count()
            quizzes_page = list(quizzes_qs[offset:offset + limit])
            
            serialized_list = []
            for quiz in quizzes_page:
                serialized_list.append({
                    'id': str(quiz.id),
                    'title': quiz.title,
                    'description': quiz.description,
                    'category': {
                        'name': quiz.category.name,
                        'slug': quiz.category.slug,
                        'color': quiz.category.color,
                        'emoji': quiz.category.emoji,
                    },
                    'difficulty': quiz.difficulty,
                    'duration_minutes': quiz.duration_minutes,
                    'total_questions': quiz.active_question_count,
                    'passing_percentage': quiz.passing_percentage,
                    'xp_per_correct': quiz.xp_per_correct,
                    'average_score': quiz.average_score,
                    'total_attempts': quiz.total_attempts,
                    'created_at': quiz.created_at.isoformat(),
                })
            return {'count': total, 'results': serialized_list}

        # Retrieve or set cache
        data = cache.get(cache_key)
        if not data:
            data = build_quiz_list()
            cache.set(cache_key, data, 900) # 15 minutes TTL

        # 2. Attach User Data (if logged in)
        if user and data['results']:
            quiz_ids = [q['id'] for q in data['results']]
            
            # Fetch attempts
            attempts_map = {}
            attempts_data = QuizAttempt.objects.filter(
                user=user,
                quiz_id__in=quiz_ids,
                status='graded'
            ).values('quiz_id', 'percentage_score')
            
            for item in attempts_data:
                qid = str(item['quiz_id'])
                if qid not in attempts_map:
                    attempts_map[qid] = {'count': 0, 'best': 0}
                attempts_map[qid]['count'] += 1
                if item['percentage_score'] > attempts_map[qid]['best']:
                    attempts_map[qid]['best'] = item['percentage_score']
            
            # Merge into results (create copy to avoid mutating cached data)
            # Actually, caching usually returns a copy/pickle, but let's be safe
            # If we modify 'data', next cache.get might return modified data if using LocMemCache?
            # Safe to modify valid dicts if we deep copy? List comprehension sufficient for top level.
            
            final_results = []
            for quiz in data['results']:
                # shallow copy
                q_copy = quiz.copy()
                u_data = attempts_map.get(q_copy['id'], {'count': 0, 'best': None})
                q_copy['user_attempts'] = u_data['count']
                q_copy['best_score'] = u_data['best']
                final_results.append(q_copy)
                
            return {
                'count': data['count'],
                'results': final_results
            }
            
        return data
    
    @staticmethod
    def get_quiz_details(quiz_id, user=None):
        """
        Get detailed quiz information.
        
        Args:
            quiz_id: UUID of quiz
            user: CustomUser instance (optional)
            
        Returns:
            tuple: (success, data, error_message)
        """
        try:
            quiz = Quiz.objects.select_related('category').get(
                id=quiz_id,
                is_published=True,
                is_active=True
            )
        except Quiz.DoesNotExist:
            return False, None, "Quiz not found"
        
        quiz_data = {
            'id': str(quiz.id),
            'title': quiz.title,
            'description': quiz.description,
            'category': {
                'name': quiz.category.name,
                'slug': quiz.category.slug,
            },
            'difficulty': quiz.difficulty,
            'duration_minutes': quiz.duration_minutes,
            'passing_percentage': quiz.passing_percentage,
            'xp_per_correct': quiz.xp_per_correct,
            'xp_per_wrong': quiz.xp_per_wrong,
            'xp_bonus_time': quiz.xp_bonus_time,
            'total_questions': quiz.questions.filter(is_active=True).count(),
            'average_score': quiz.average_score,
            'pass_rate': quiz.pass_rate,
            'total_attempts': quiz.total_attempts,
            'unique_users': quiz.unique_users,
        }
        
        if user:
            # User's attempts on this quiz
            user_attempts = QuizAttempt.objects.filter(
                quiz=quiz,
                user=user
            ).order_by('-started_at')[:5]
            
            quiz_data['user_attempts'] = [
                {
                    'id': str(attempt.id),
                    'score': attempt.percentage_score,
                    'passed': attempt.is_passed,
                    'xp_earned': attempt.xp_earned,
                    'attempted_at': attempt.started_at.isoformat(),
                }
                for attempt in user_attempts
            ]
        
        return True, quiz_data, None
    
    @staticmethod
    @transaction.atomic
    def start_quiz(user, quiz_id):
        """
        Start a new quiz attempt.
        
        Args:
            user: CustomUser instance
            quiz_id: UUID of quiz
            
        Returns:
            tuple: (success, data, error_message)
        """
        try:
            quiz = Quiz.objects.select_related('category').prefetch_related(
                Prefetch(
                    'questions',
                    queryset=Question.objects.filter(is_active=True).order_by('sequence')
                )
            ).get(id=quiz_id, is_published=True, is_active=True)
        except Quiz.DoesNotExist:
            logger.warning(f"Quiz not found: {quiz_id}")
            return False, None, "Quiz not found"
        
        # Get active questions
        questions = list(quiz.questions.filter(is_active=True).order_by('sequence'))
        
        if not questions:
            logger.warning(f"Quiz has no active questions: {quiz_id}")
            return False, None, "Quiz has no questions"
        
        # Check Daily Challenge Limit (1 Attempt)
        if quiz.category.slug == 'daily-challenge':
            if QuizAttempt.objects.filter(user=user, quiz=quiz).exists():
                 return False, None, "Daily challenges can only be attempted once."
        
        # Create quiz attempt
        attempt = QuizAttempt.objects.create(
            user=user,
            quiz=quiz,
            total_questions=len(questions),
            status='started'
        )
        
        # Create answer records for all questions
        for question in questions:
            Answer.objects.create(
                attempt=attempt,
                question=question
            )
        
        # Update quiz stats
        quiz.total_attempts = F('total_attempts') + 1
        quiz.save(update_fields=['total_attempts'])
        
        # Update user profile
        try:
            user.profile.total_quizzes_attempted = F('total_quizzes_attempted') + 1
            user.profile.save(update_fields=['total_quizzes_attempted'])
        except:
            pass
        
        logger.info(f"Quiz attempt started: {attempt.id} for user {user.email}")
        
        # Format questions for response (hide correct answers)
        questions_data = [
            {
                'id': str(q.id),
                'text': q.text,
                'sequence': q.sequence,
                'options': [
                    {'id': 'A', 'text': q.option_a},
                    {'id': 'B', 'text': q.option_b},
                    {'id': 'C', 'text': q.option_c},
                    {'id': 'D', 'text': q.option_d},
                ]
            }
            for q in questions
        ]
        
        return True, {
            'attempt_id': str(attempt.id),
            'quiz': {
                'id': str(quiz.id),
                'title': quiz.title,
                'duration_minutes': quiz.duration_minutes,
                'total_questions': len(questions),
            },
            'questions': questions_data,
            'started_at': attempt.started_at.isoformat(),
        }, None
    
    @staticmethod
    @transaction.atomic
    def save_answer(attempt_id, question_id, selected_answer):
        """
        Save user's answer to a question.
        
        Args:
            attempt_id: UUID of quiz attempt
            question_id: UUID of question
            selected_answer: Choice (A/B/C/D)
            
        Returns:
            tuple: (success, data, error_message)
        """
        try:
            answer = Answer.objects.select_related('question').get(
                attempt_id=attempt_id,
                question_id=question_id
            )
        except Answer.DoesNotExist:
            return False, None, "Answer record not found"
        
        # Validate answer choice
        if selected_answer not in ['A', 'B', 'C', 'D']:
            return False, None, "Invalid answer choice"
        
        # Save answer
        answer.selected_answer = selected_answer
        answer.is_correct = (selected_answer == answer.question.correct_answer)
        answer.save(update_fields=['selected_answer', 'is_correct'])
        
        return True, {
            'question_id': str(question_id),
            'saved': True
        }, None
    
    @staticmethod
    @transaction.atomic
    def submit_quiz(attempt_id):
        """
        Submit quiz for grading and calculate score.
        
        Args:
            attempt_id: UUID of quiz attempt
            
        Returns:
            tuple: (success, data, error_message)
        """
        try:
            attempt = QuizAttempt.objects.select_related('quiz', 'user').get(id=attempt_id)
        except QuizAttempt.DoesNotExist:
            return False, None, "Quiz attempt not found"
        
        if attempt.status == 'graded':
            return False, None, "Quiz already submitted"
        
        # Get all answers for this attempt
        answers = Answer.objects.filter(attempt=attempt).select_related('question')
        
        # Calculate scores
        correct_count = answers.filter(is_correct=True).count()
        wrong_count = answers.filter(
            selected_answer__isnull=False,
            is_correct=False
        ).count()
        unanswered_count = answers.filter(selected_answer__isnull=True).count()
        
        # Calculate percentage
        total_questions = attempt.total_questions
        percentage_score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        # Check if passed
        is_passed = percentage_score >= attempt.quiz.passing_percentage
        
        # Calculate duration
        now = timezone.now()
        duration = (now - attempt.started_at).total_seconds()
        expected_duration = attempt.quiz.duration_minutes * 60
        
        # Calculate XP
        xp_base = correct_count * attempt.quiz.xp_per_correct
        xp_base += wrong_count * attempt.quiz.xp_per_wrong
        
        # Time bonus (if completed in 75% of time)
        xp_time_bonus = 0
        if duration <= (expected_duration * 0.75):
            xp_time_bonus = attempt.quiz.xp_bonus_time
        
        # Accuracy bonus
        xp_accuracy_bonus = 0
        if percentage_score == 100:
            xp_accuracy_bonus = 10
        elif percentage_score >= 90:
            xp_accuracy_bonus = 5
        
        total_xp = xp_base + xp_time_bonus + xp_accuracy_bonus
        
        # Update attempt
        attempt.status = 'graded'
        attempt.submitted_at = now
        attempt.graded_at = now
        attempt.correct_count = correct_count
        attempt.wrong_count = wrong_count
        attempt.unanswered_count = unanswered_count
        attempt.percentage_score = percentage_score
        attempt.is_passed = is_passed
        attempt.duration_seconds = int(duration)
        attempt.xp_base = xp_base
        attempt.xp_time_bonus = xp_time_bonus
        attempt.xp_accuracy_bonus = xp_accuracy_bonus
        attempt.xp_earned = total_xp
        attempt.save()
        
        # Update quiz stats
        all_attempts = QuizAttempt.objects.filter(
            quiz=attempt.quiz,
            status='graded'
        )
        
        attempt.quiz.average_score = all_attempts.aggregate(Avg('percentage_score'))['percentage_score__avg'] or 0
        attempt.quiz.pass_rate = (all_attempts.filter(is_passed=True).count() / all_attempts.count() * 100) if all_attempts.count() > 0 else 0
        attempt.quiz.save(update_fields=['average_score', 'pass_rate'])
        
        # Update user profile accuracy and total attempts
        try:
            user_attempts = QuizAttempt.objects.filter(
                user=attempt.user,
                status='graded'
            )
            avg_accuracy = user_attempts.aggregate(Avg('percentage_score'))['percentage_score__avg'] or 0
            
            # Increment attempts
            from django.db.models import F
            attempt.user.profile.total_quizzes_attempted = F('total_quizzes_attempted') + 1
            attempt.user.profile.accuracy_percentage = avg_accuracy
            attempt.user.profile.save(update_fields=['accuracy_percentage', 'total_quizzes_attempted'])
            
            # Refresh profile to ensure in-memory object is up to date for badge check
            attempt.user.profile.refresh_from_db()
            
            # Also update UserStats
            try:
                stats = attempt.user.stats
                stats.quizzes_attempted = F('quizzes_attempted') + 1
                if is_passed:
                    stats.quizzes_passed = F('quizzes_passed') + 1
                stats.save(update_fields=['quizzes_attempted', 'quizzes_passed'] if is_passed else ['quizzes_attempted'])
                # Refresh stats
                attempt.user.stats.refresh_from_db()
            except:
                pass
                
        except Exception as e:
            logger.warning(f"Could not update user stats: {e}")

        # Award XP to user (if XP system is available)
        try:
            from xp_system.services import XPService
            XPService.award_xp(attempt.user, total_xp, f'Quiz completed: {attempt.quiz.title}', quiz_attempt_id=attempt.id)
            
            # Update streak
            XPService.update_streak(attempt.user)
            
        except Exception as e:
            logger.warning(f"Could not award XP or update streak: {e}")
        
        logger.info(f"Quiz submitted: {attempt.id}, Score: {percentage_score}%, XP: {total_xp}")
        
        # Return detailed results
        return True, {
            'attempt_id': str(attempt.id),
            'quiz': {
                'id': str(attempt.quiz.id),
                'title': attempt.quiz.title,
            },
            'score': {
                'correct': correct_count,
                'wrong': wrong_count,
                'unanswered': unanswered_count,
                'total': total_questions,
                'percentage': percentage_score,
            },
            'is_passed': is_passed,
            'xp': {
                'base': xp_base,
                'time_bonus': xp_time_bonus,
                'accuracy_bonus': xp_accuracy_bonus,
                'total': total_xp,
            },
            'duration_seconds': int(duration),
            'submitted_at': now.isoformat(),
        }, None
    
    @staticmethod
    def get_quiz_results(attempt_id, user=None):
        """
        Get detailed quiz results with answers.
        
        Args:
            attempt_id: UUID of quiz attempt
            user: CustomUser instance (for verification)
            
        Returns:
            tuple: (success, data, error_message)
        """
        try:
            attempt = QuizAttempt.objects.select_related('quiz', 'user').get(id=attempt_id)
        except QuizAttempt.DoesNotExist:
            return False, None, "Quiz attempt not found"
        
        # Verify user owns this attempt
        if user and attempt.user != user:
            return False, None, "Unauthorized"
        
        if attempt.status != 'graded':
            return False, None, "Quiz not yet graded"
        
        # Get all answers with details
        answers = Answer.objects.filter(attempt=attempt).select_related('question').order_by('question__sequence')
        
        questions_results = []
        for answer in answers:
            q = answer.question
            questions_results.append({
                'question_id': str(q.id),
                'sequence': q.sequence,
                'text': q.text,
                'explanation': q.explanation,
                'options': {
                    'A': q.option_a,
                    'B': q.option_b,
                    'C': q.option_c,
                    'D': q.option_d,
                },
                'correct_answer': q.correct_answer,
                'user_answer': answer.selected_answer,
                'is_correct': answer.is_correct,
                'is_correct': answer.is_correct,
                'time_spent': answer.time_spent_seconds,
            })
            
        # Check for Major Rank Up Animation
        rank_up_animation = None
        try:
            from dashboard.models import UserActivityLog
            # Look for recent rank up activity (created within last 10 minutes)
            # Increased window to ensure we catch it even if there's a delay
            recent_time = timezone.now() - timedelta(minutes=10)
            activity = UserActivityLog.objects.filter(
                user=user,
                activity_type='rank_change',
                created_at__gte=recent_time
            ).order_by('-created_at').first()
            
            if activity:
                # Check for explicitly True or just presence if logic was fuzzy
                if activity.metadata.get('major_rank_up'):
                    rank_up_animation = activity.metadata
                else:
                     logger.info(f"Rank change found but major_rank_up is false for {user.email}")
            
        except Exception as e:
            logger.warning(f"Error checking rank up animation: {e}")
        
        return True, {
            'attempt_id': str(attempt.id),
            'quiz': {
                'id': str(attempt.quiz.id),
                'title': attempt.quiz.title,
                'difficulty': attempt.quiz.difficulty,
            },
            'user': {
                'id': str(attempt.user.id),
                'name': attempt.user.full_name,
            },
            'score': {
                'correct': attempt.correct_count,
                'wrong': attempt.wrong_count,
                'unanswered': attempt.unanswered_count,
                'total': attempt.total_questions,
                'percentage': attempt.percentage_score,
            },
            'is_passed': attempt.is_passed,
            'xp_earned': attempt.xp_earned,
            'duration_seconds': attempt.duration_seconds,
            'started_at': attempt.started_at.isoformat(),
            'submitted_at': attempt.submitted_at.isoformat() if attempt.submitted_at else None,
            'questions': questions_results,
            'rank_up_animation': rank_up_animation, # New field
        }, None

    @staticmethod
    def get_attempt_context(attempt_id, user):
        """
        Get active attempt context (questions without answers) for resuming.
        
        Args:
            attempt_id: UUID of quiz attempt
            user: CustomUser instance
            
        Returns:
            tuple: (success, data, error_message)
        """
        try:
            attempt = QuizAttempt.objects.select_related('quiz').get(id=attempt_id)
        except QuizAttempt.DoesNotExist:
            return False, None, "Quiz attempt not found"
        
        # Verify ownership
        if attempt.user != user:
            return False, None, "Unauthorized"
            
        # Get active questions
        questions = list(attempt.quiz.questions.filter(is_active=True).order_by('sequence'))
        
        questions_data = [
            {
                'id': str(q.id),
                'text': q.text,
                'sequence': q.sequence,
                'options': [
                    {'id': 'A', 'text': q.option_a},
                    {'id': 'B', 'text': q.option_b},
                    {'id': 'C', 'text': q.option_c},
                    {'id': 'D', 'text': q.option_d},
                ]
            }
            for q in questions
        ]
        
        return True, {
            'attempt_id': str(attempt.id),
            'quiz': {
                'id': str(attempt.quiz.id),
                'title': attempt.quiz.title,
                'duration_minutes': attempt.quiz.duration_minutes,
                'total_questions': len(questions),
            },
            'questions': questions_data,
            'started_at': attempt.started_at.isoformat(),
            'status': attempt.status
        }, None
