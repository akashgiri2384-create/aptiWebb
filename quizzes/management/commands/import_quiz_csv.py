from django.core.management.base import BaseCommand
from django.utils import timezone
from quizzes.models import Quiz, Question, Category
from daily_quizzes.models import DailyQuiz
import csv
import os

class Command(BaseCommand):
    help = 'Import quiz questions from CSV and optionally schedule as Daily Quiz'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')
        parser.add_argument('quiz_title', type=str, help='Title of the quiz')
        parser.add_argument('--category', type=str, default='General', help='Category name')
        parser.add_argument('--daily', action='store_true', help='Schedule as Today\'s Daily Quiz')
        parser.add_argument('--slot', type=str, default='morning', choices=['morning', 'evening'], help='Daily quiz slot')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        quiz_title = options['quiz_title']
        category_name = options['category']
        is_daily = options['daily']
        slot = options['slot']

        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file_path}'))
            return

        # Get or Create Category
        category, _ = Category.objects.get_or_create(
            name=category_name,
            defaults={'slug': category_name.lower().replace(' ', '-')}
        )

        # Create Quiz
        quiz, created = Quiz.objects.get_or_create(
            title=quiz_title,
            defaults={
                'category': category,
                'description': f'Imported from CSV',
                'difficulty': 'medium',
                'duration_minutes': 10,
                'is_published': True
            }
        )

        if not created:
             self.stdout.write(self.style.WARNING(f'Quiz "{quiz_title}" already exists. Appending questions.'))

        # Import Questions
        # Determine starting sequence
        from django.db.models import Max
        max_seq = Question.objects.filter(quiz=quiz).aggregate(Max('sequence'))['sequence__max']
        current_seq = (max_seq or 0) + 1
        count = 0

        try:
            with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                # Expected columns: question, option_a, option_b, option_c, option_d, correct_answer, explanation
                
                for row in reader:
                    Question.objects.create(
                        quiz=quiz,
                        text=row.get('question', '').strip(),
                        option_a=row.get('option_a', '').strip(),
                        option_b=row.get('option_b', '').strip(),
                        option_c=row.get('option_c', '').strip(),
                        option_d=row.get('option_d', '').strip(),
                        correct_answer=row.get('correct_answer', 'A').upper(),
                        explanation=row.get('explanation', '').strip(),
                        sequence=current_seq
                    )
                    current_seq += 1
                    count += 1
            
            # Update Quiz Stats
            quiz.total_questions = Question.objects.filter(quiz=quiz).count()
            quiz.save()
            
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} questions to "{quiz_title}"'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading CSV: {e}'))
            return

        # Schedule Daily Quiz
        if is_daily:
            today = timezone.now().date()
            daily, d_created = DailyQuiz.objects.update_or_create(
                date=today,
                slot=slot,
                defaults={
                    'quiz': quiz,
                    'quiz_title': quiz_title,
                    'is_active': True,
                    'keys_required': 5 # System default
                }
            )
            action = "Created" if d_created else "Updated"
            self.stdout.write(self.style.SUCCESS(f'{action} Daily Quiz for {today} ({slot})'))
