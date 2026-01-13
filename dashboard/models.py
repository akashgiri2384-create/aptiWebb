"""
Dashboard models for user activity tracking and daily metrics.

Models:
- UserActivityLog: Audit trail of all user activities
- DailyActivityMetric: Aggregated daily statistics for performance
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class UserActivityLog(models.Model):
    """
    Log all user activities for audit trail and analytics.
    
    Tracks every user action including quiz attempts, XP earning,
    key transactions, rank changes, and badge unlocks.
    """
    
    ACTIVITY_TYPES = [
        ('quiz_start', 'Quiz Started'),
        ('quiz_complete', 'Quiz Completed'),
        ('quiz_passed', 'Quiz Passed'),
        ('quiz_failed', 'Quiz Failed'),
        ('xp_earned', 'XP Earned'),
        ('key_earned', 'Key Earned'),
        ('key_used', 'Key Used'),
        ('daily_quiz_unlock', 'Daily Quiz Unlocked'),
        ('ad_watched', 'Ad Watched'),
        ('rank_change', 'Rank Changed'),
        ('badge_unlocked', 'Badge Unlocked'),
        ('streak_update', 'Streak Updated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )
    
    # Activity details
    activity_type = models.CharField(
        'Activity Type',
        max_length=50,
        choices=ACTIVITY_TYPES,
        db_index=True
    )
    description = models.CharField('Description', max_length=255)
    
    # Associated data (flexible)
    quiz_id = models.UUIDField('Quiz ID', null=True, blank=True, db_index=True)
    xp_change = models.IntegerField('XP Change', default=0)
    key_change = models.IntegerField('Key Change', default=0)
    rank_change = models.IntegerField('Rank Change', null=True, blank=True)
    badge_id = models.UUIDField('Badge ID', null=True, blank=True)
    
    # Metadata (flexible JSON for additional data)
    metadata = models.JSONField('Metadata', default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'dashboard_useractivitylog'
        verbose_name = 'User Activity Log'
        verbose_name_plural = 'User Activity Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
            models.Index(fields=['user', 'activity_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()} - {self.created_at}"


class DailyActivityMetric(models.Model):
    """
    Aggregated daily metrics for performance optimization.
    
    Pre-calculates and stores daily stats to avoid expensive
    real-time aggregation queries. Updated via Celery task.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='daily_metrics'
    )
    
    # Date tracking
    date = models.DateField('Date', db_index=True)
    
    # Quiz metrics
    quizzes_attempted = models.IntegerField('Quizzes Attempted', default=0)
    questions_answered = models.IntegerField('Questions Answered', default=0)
    correct_answers = models.IntegerField('Correct Answers', default=0)
    wrong_answers = models.IntegerField('Wrong Answers', default=0)
    
    # Performance
    accuracy_percentage = models.FloatField('Accuracy %', default=0.0)
    xp_earned = models.IntegerField('XP Earned', default=0)
    xp_spent = models.IntegerField('XP Spent', default=0)
    keys_earned = models.IntegerField('Keys Earned', default=0)
    keys_used = models.IntegerField('Keys Used', default=0)
    
    # Time tracking
    total_time_minutes = models.IntegerField('Total Time (minutes)', default=0)
    
    # Badges
    badges_earned = models.IntegerField('Badges Earned', default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_dailyactivitymetric'
        verbose_name = 'Daily Activity Metric'
        verbose_name_plural = 'Daily Activity Metrics'
        ordering = ['-date']
        unique_together = ('user', 'date')
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['-date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.date}"
    
    def calculate_accuracy(self):
        """Calculate accuracy percentage."""
        total = self.correct_answers + self.wrong_answers
        if total == 0:
            return 0.0
        return round((self.correct_answers / total) * 100, 2)
    
    def save(self, *args, **kwargs):
        """Auto-calculate accuracy on save."""
        self.accuracy_percentage = self.calculate_accuracy()
        super().save(*args, **kwargs)
