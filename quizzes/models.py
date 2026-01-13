"""
Quiz engine models.

Models:
- Category: Quiz category classification
- Quiz: Quiz configuration and metadata
- Question: Multiple choice questions
- QuizAttempt: User's quiz attempt session
- Answer: User's answer to a question
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
import uuid

User = get_user_model()


class Category(models.Model):
    """
    Quiz category classification.
    
    Organizes quizzes into categories with custom styling.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField('Name', max_length=100, unique=True, db_index=True)
    slug = models.SlugField('Slug', unique=True, max_length=100)
    description = models.TextField('Description', blank=True)
    
    # Styling
    color = models.CharField('Color', max_length=7, default='#2B8080', help_text='Hex color code')
    icon = models.CharField('Icon', max_length=50, blank=True, help_text='Icon class name')
    emoji = models.CharField('Emoji', max_length=10, blank=True)
    
    # Metadata
    is_active = models.BooleanField('Active', default=True, db_index=True)
    order = models.IntegerField('Display Order', default=0)
    
    # Statistics (denormalized)
    total_quizzes = models.IntegerField('Total Quizzes', default=0)
    total_attempts = models.IntegerField('Total Attempts', default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quizzes_category'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'order']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Quiz(models.Model):
    """
    Quiz configuration and metadata.
    
    Contains all quiz settings, XP configuration, and performance statistics.
    """
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic information
    title = models.CharField('Title', max_length=255, db_index=True)
    description = models.TextField('Description')
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    
    # Configuration
    difficulty = models.CharField('Difficulty', max_length=20, choices=DIFFICULTY_CHOICES)
    duration_minutes = models.IntegerField('Duration (minutes)', default=30)
    passing_percentage = models.IntegerField('Passing %', default=50, help_text='0-100')
    
    # XP configuration
    xp_per_correct = models.IntegerField('XP per Correct Answer', default=10)
    xp_per_wrong = models.IntegerField('XP per Wrong Answer', default=0)
    xp_bonus_time = models.IntegerField('Time Bonus XP', default=5, help_text='Bonus if completed in 75% of time')
    
    # Status
    is_published = models.BooleanField('Published', default=False, db_index=True)
    is_active = models.BooleanField('Active', default=True, db_index=True)
    
    # Statistics (denormalized)
    total_attempts = models.IntegerField('Total Attempts', default=0)
    unique_users = models.IntegerField('Unique Users', default=0)
    average_score = models.FloatField('Average Score %', default=0.0)
    average_time_seconds = models.IntegerField('Average Time (seconds)', default=0)
    pass_rate = models.FloatField('Pass Rate %', default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quizzes_quiz'
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'
        ordering = ['-is_published', '-created_at']
        indexes = [
            models.Index(fields=['category', 'is_published']),
            models.Index(fields=['is_active', 'is_published']),
        ]
    
    def __str__(self):
        return self.title


class Question(models.Model):
    """
    Multiple choice question.
    
    Contains question text, 4 options (A-D), correct answer, and explanation.
    """
    
    ANSWER_CHOICES = [
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    
    # Question content
    text = models.TextField('Question Text')
    explanation = models.TextField('Explanation')
    
    # Options
    option_a = models.CharField('Option A', max_length=500)
    option_b = models.CharField('Option B', max_length=500)
    option_c = models.CharField('Option C', max_length=500)
    option_d = models.CharField('Option D', max_length=500)
    
    # Correct answer
    correct_answer = models.CharField('Correct Answer', max_length=1, choices=ANSWER_CHOICES)
    
    # Sequencing
    sequence = models.IntegerField('Sequence', db_index=True)
    
    # Status
    is_active = models.BooleanField('Active', default=True, db_index=True)
    
    # Statistics (denormalized)
    total_attempts = models.IntegerField('Total Attempts', default=0)
    correct_count = models.IntegerField('Correct Answers', default=0)
    difficulty_index = models.FloatField('Difficulty Index', default=0.5, help_text='0 (easy) to 1 (hard)')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quizzes_question'
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['quiz', 'sequence']
        unique_together = ('quiz', 'sequence')
        indexes = [
            models.Index(fields=['quiz', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.quiz.title} - Q{self.sequence}"


class QuizAttempt(models.Model):
    """
    User's quiz attempt session.
    
    Tracks attempt status, scoring, XP earned, and timing.
    """
    
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # References
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    
    # Status
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='started', db_index=True)
    
    # Scoring
    total_questions = models.IntegerField('Total Questions')
    correct_count = models.IntegerField('Correct Answers', default=0)
    wrong_count = models.IntegerField('Wrong Answers', default=0)
    unanswered_count = models.IntegerField('Unanswered', default=0)
    
    # Results
    percentage_score = models.FloatField('Score %', default=0.0)
    is_passed = models.BooleanField('Passed', default=False, db_index=True)
    
    # XP breakdown
    xp_earned = models.IntegerField('Total XP Earned', default=0)
    xp_from_correct = models.IntegerField('XP from Correct', default=0)
    xp_from_wrong = models.IntegerField('XP from Wrong', default=0)
    xp_bonus = models.IntegerField('Time Bonus XP', default=0)
    
    # Time tracking
    started_at = models.DateTimeField('Started At', auto_now_add=True)
    submitted_at = models.DateTimeField('Submitted At', null=True, blank=True)
    duration_seconds = models.IntegerField('Duration (seconds)', null=True, blank=True)
    
    # Timestamps
    graded_at = models.DateTimeField('Graded At', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'quizzes_quizattempt'
        verbose_name = 'Quiz Attempt'
        verbose_name_plural = 'Quiz Attempts'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'quiz', '-started_at']),
            models.Index(fields=['user', 'is_passed']),
            models.Index(fields=['quiz', '-started_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.quiz.title} ({self.get_status_display()})"


class Answer(models.Model):
    """
    User's answer to a question.
    
    Records selected answer, correctness, and time spent.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # References
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='user_answers'
    )
    
    # Response
    selected_answer = models.CharField('Selected Answer', max_length=1, null=True, blank=True, help_text='A, B, C, or D')
    is_correct = models.BooleanField('Is Correct', default=False)
    
    # Time tracking
    time_spent_seconds = models.IntegerField('Time Spent (seconds)', default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'quizzes_answer'
        verbose_name = 'Answer'
        verbose_name_plural = 'Answers'
        unique_together = ('attempt', 'question')
        ordering = ['question__sequence']
        indexes = [
            models.Index(fields=['attempt', 'is_correct']),
        ]
    
    def __str__(self):
        return f"{self.attempt.user.email} - Q{self.question.sequence} - {self.selected_answer or 'No answer'}"
