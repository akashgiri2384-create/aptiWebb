"""Django admin configuration for quizzes app"""
from django.contrib import admin
from django import forms
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
import csv
import io

from .models import Category, Quiz, Question, QuizAttempt, Answer
from daily_quizzes.models import DailyQuiz

class CsvImportForm(forms.Form):
    title = forms.CharField(label="Quiz Title", max_length=255)
    csv_file = forms.FileField(label="Questions CSV", help_text="Cols: question,option_a,option_b,option_c,option_d,correct_answer,explanation")
    category = forms.ModelChoiceField(queryset=Category.objects.all())
    
    # Daily Quiz Options
    is_daily = forms.BooleanField(required=False, label="Schedule as Daily Quiz?", initial=False)
    daily_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), help_text="Required if Daily Quiz selected")
    daily_slot = forms.ChoiceField(choices=[('morning', 'Morning'), ('evening', 'Evening'), ('night', 'Night')], required=False, initial='morning')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'emoji', 'total_quizzes', 'is_active', 'order']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_active']
    ordering = ['order', 'name']

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    fields = ['text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'explanation', 'sequence', 'is_active']

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    change_list_template = "admin/quizzes/quiz/change_list.html"
    list_display = ['title', 'category', 'difficulty', 'is_published', 'total_questions_display', 'total_attempts', 'pass_rate']
    list_filter = ['category', 'difficulty', 'is_published']
    search_fields = ['title']
    inlines = [QuestionInline]

    def total_questions_display(self, obj):
        return obj.questions.filter(is_active=True).count()
    total_questions_display.short_description = 'Questions'

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='quizzes_quiz_import_csv'),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                title = form.cleaned_data["title"]
                csv_file = form.cleaned_data["csv_file"]
                category = form.cleaned_data["category"]
                is_daily = form.cleaned_data["is_daily"]
                daily_date = form.cleaned_data["daily_date"]
                daily_slot = form.cleaned_data["daily_slot"]

                try:
                    # Create Quiz
                    quiz = Quiz.objects.create(
                        title=title,
                        category=category,
                        description="Imported from CSV",
                        difficulty='medium',
                        duration_minutes=10,
                        is_published=True
                        # total_questions is calculated dynamically
                    )
                    
                    # Parse CSV
                    decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
                    reader = csv.DictReader(decoded_file)
                    
                    count = 0
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
                            sequence=count + 1
                        )
                        count += 1
                        
                    quiz.total_questions = count
                    quiz.save()
                    
                    msg = f"Imported {count} questions for '{title}'."
                    
                    # Schedule Daily
                    if is_daily:
                        if not daily_date:
                            raise ValueError("Date is required for Daily Quiz")
                            
                        DailyQuiz.objects.update_or_create(
                            date=daily_date,
                            slot=daily_slot,
                            defaults={
                                'quiz': quiz,
                                'quiz_title': title, # Legacy
                                'is_active': True,
                                'keys_required': 5
                            }
                        )
                        msg += f" Scheduled as Daily Quiz for {daily_date} ({daily_slot})."

                    messages.success(request, msg)
                    return redirect("..")
                    
                except Exception as e:
                    messages.error(request, f"Error: {str(e)}")
                    
        else:
            form = CsvImportForm()
            
        context = {
            "form": form,
            "title": "Import Quiz from CSV",
            "opts": self.model._meta,
            # Standard admin context
            "site_header": self.admin_site.site_header,
        }
        return render(request, "admin/quizzes/quiz/import_csv.html", context)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'sequence', 'text_preview', 'correct_answer', 'is_active']
    list_filter = ['quiz', 'is_active']
    ordering = ['quiz', 'sequence']
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'status', 'percentage_score', 'is_passed', 'xp_earned', 'started_at']
    list_filter = ['status', 'is_passed', 'started_at']
    readonly_fields = ['user', 'quiz', 'total_questions', 'correct_count', 'percentage_score']

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'selected_answer', 'is_correct', 'time_spent_seconds']
    list_filter = ['is_correct']
