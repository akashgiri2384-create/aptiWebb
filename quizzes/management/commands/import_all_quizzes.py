from django.core.management.base import BaseCommand
import os
import csv
from django.conf import settings
from quizzes.models import Category, Quiz, Question
from django.db import transaction

class Command(BaseCommand):
    help = 'Import quizzes from CSV files in D:\\aptiWeb\\apti_app_questions'

    def handle(self, *args, **kwargs):
        base_dir = r'D:\aptiWeb\apti_app_questions'
        
        if not os.path.exists(base_dir):
            self.stdout.write(self.style.ERROR(f'Directory not found: {base_dir}'))
            return

        self.stdout.write(f"Scanning {base_dir}...")

        # Walk through the directory structure
        for root, dirs, files in os.walk(base_dir):
            # Skip the root folder itself, only process subfolders which act as Categories
            if root == base_dir:
                continue
                
            folder_name = os.path.basename(root)
            self.stdout.write(self.style.WARNING(f"\nProcessing Category: {folder_name}"))
            
            # 1. Get or Create Category
            # Using partial matching or cleaner names if needed, but direct mapping is safest for now
            category, created = Category.objects.get_or_create(
                name__iexact=folder_name,
                defaults={
                    'name': folder_name,
                    'description': f'Quizzes related to {folder_name}',
                    'icon': 'fa-book', # Default icon
                    'color': '#4F46E5' # Default color
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created new category: {category.name}"))
            else:
                self.stdout.write(f"  Found existing category: {category.name}")

            # 2. Process CSV files in this folder
            for file in files:
                if not file.lower().endswith('.csv'):
                    continue
                    
                quiz_title = os.path.splitext(file)[0]
                file_path = os.path.join(root, file)
                
                self.import_quiz(file_path, quiz_title, category)

    def import_quiz(self, file_path, quiz_title, category):
        # Check if quiz already exists to avoid duplication
        if Quiz.objects.filter(title=quiz_title, category=category).exists():
            self.stdout.write(f"    Skipping existing quiz: {quiz_title}")
            return

        self.stdout.write(f"    Importing Quiz: {quiz_title}...")
        
        try:
            with transaction.atomic():
                # Create Quiz
                quiz = Quiz.objects.create(
                    title=quiz_title,
                    description=f"Practice details for {quiz_title}",
                    category=category,
                    difficulty='medium',
                    duration_minutes=15, # Default
                    passing_percentage=50,
                    is_active=True,
                    is_published=True
                )
                
                # Parse CSV
                questions_to_create = []
                with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
                    reader = csv.DictReader(csvfile)
                    
                    # Normalize headers (strip whitespace/bom)
                    reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
                    
                    if 'question' not in reader.fieldnames or 'correct_answer' not in reader.fieldnames:
                        self.stdout.write(self.style.ERROR(f"    Invalid CSV Format in {quiz_title}: Missing generic headers"))
                        return

                    for index, row in enumerate(reader, 1):
                        # Map correct answer (Handle 'Option A' or 'A')
                        raw_ans = row.get('correct_answer', '').strip().upper()
                        clean_ans = raw_ans
                        
                        if 'OPTION A' in raw_ans or raw_ans == 'A': clean_ans = 'A'
                        elif 'OPTION B' in raw_ans or raw_ans == 'B': clean_ans = 'B'
                        elif 'OPTION C' in raw_ans or raw_ans == 'C': clean_ans = 'C'
                        elif 'OPTION D' in raw_ans or raw_ans == 'D': clean_ans = 'D'
                        
                        if clean_ans not in ['A', 'B', 'C', 'D']:
                            clean_ans = 'A' # Fallback default
                            
                        question = Question(
                            quiz=quiz,
                            text=row.get('question', '').strip(),
                            option_a=row.get('option_a', '').strip(),
                            option_b=row.get('option_b', '').strip(),
                            option_c=row.get('option_c', '').strip(),
                            option_d=row.get('option_d', '').strip(),
                            correct_answer=clean_ans,
                            explanation=row.get('explanation', '').strip(),
                            sequence=index,
                            is_active=True
                        )
                        questions_to_create.append(question)
                
                # Bulk create questions
                Question.objects.bulk_create(questions_to_create)
                self.stdout.write(self.style.SUCCESS(f"    Successfully imported {len(questions_to_create)} questions for {quiz_title}"))
                
                # Update Category Stats
                category.total_quizzes += 1
                category.save()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"    Failed to import {quiz_title}: {str(e)}"))
