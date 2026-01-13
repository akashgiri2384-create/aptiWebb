"""
Analytics and reporting models - COMPLETE IMPLEMENTATION.

Models:
- AnalyticsSnapshot: Daily platform aggregates
- UserReport: Weekly/monthly user reports
- PlatformMetrics: Platform-wide performance
- CollegeAnalytics: College-specific metrics
"""

from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class AnalyticsSnapshot(models.Model):
    """Daily snapshot of platform analytics."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Date
    date = models.DateField('Date', auto_now_add=True, db_index=True)
    
    # User metrics
    total_users = models.IntegerField('Total Users', default=0)
    active_users = models.IntegerField('Active Users (24h)', default=0)
    new_users = models.IntegerField('New Users', default=0)
    
    # Activity metrics
    total_attempts = models.IntegerField('Total Attempts', default=0)
    successful_attempts = models.IntegerField('Successful Attempts', default=0)
    failed_attempts = models.IntegerField('Failed Attempts', default=0)
    
    # Quiz metrics
    quizzes_created = models.IntegerField('Quizzes Created', default=0)
    quizzes_published = models.IntegerField('Quizzes Published', default=0)
    
    # XP metrics
    total_xp_distributed = models.IntegerField('Total XP Distributed', default=0)
    avg_xp_per_user = models.FloatField('Avg XP per User', default=0.0)
    
    # Engagement
    avg_accuracy = models.FloatField('Avg Accuracy %', default=0.0)
    avg_completion_time = models.FloatField('Avg Completion Time (s)', default=0.0)
    
    # Device metrics
    mobile_users = models.IntegerField('Mobile Users', default=0)
    desktop_users = models.IntegerField('Desktop Users', default=0)
    
    class Meta:
        db_table = 'analytics_analyticssnapshot'
        verbose_name = 'Analytics Snapshot'
        verbose_name_plural = 'Analytics Snapshots'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date']),
        ]
    
    def __str__(self):
        return f"Analytics: {self.date}"


class UserReport(models.Model):
    """Weekly/monthly user performance report."""
    
    REPORT_TYPE_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    
    # Report type
    report_type = models.CharField('Type', max_length=20, choices=REPORT_TYPE_CHOICES, db_index=True)
    
    # Period
    period_start = models.DateField('Period Start', db_index=True)
    period_end = models.DateField('Period End')
    
    # Metrics
    quizzes_attempted = models.IntegerField('Quizzes Attempted', default=0)
    quizzes_passed = models.IntegerField('Quizzes Passed', default=0)
    quizzes_failed = models.IntegerField('Quizzes Failed', default=0)
    
    total_xp_earned = models.IntegerField('Total XP Earned', default=0)
    total_xp_spent = models.IntegerField('Total XP Spent', default=0)
    avg_accuracy = models.FloatField('Avg Accuracy %', default=0.0)
    avg_completion_time = models.FloatField('Avg Completion Time (s)', default=0.0)
    
    # Ranking
    rank_overall = models.IntegerField('Overall Rank', null=True, blank=True)
    rank_percentile = models.FloatField('Percentile', default=0.0)
    
    # Streak
    longest_streak = models.IntegerField('Longest Streak', default=0)
    
    # Badges
    badges_unlocked = models.IntegerField('Badges Unlocked', default=0)
    
    # Report content
    report_data = models.JSONField('Report Data', default=dict, help_text='Detailed breakdown')
    
    # Status
    is_sent = models.BooleanField('Sent', default=False)
    sent_at = models.DateTimeField('Sent At', null=True, blank=True)
    pdf_file = models.FileField('PDF File', upload_to='reports/pdf/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_userreport'
        verbose_name = 'User Report'
        verbose_name_plural = 'User Reports'
        ordering = ['-period_start']
        unique_together = ('user', 'report_type', 'period_start')
        indexes = [
            models.Index(fields=['user', '-period_start']),
            models.Index(fields=['report_type', '-period_start']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_report_type_display()} ({self.period_start})"


class PlatformMetrics(models.Model):
    """Platform-wide performance metrics."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Date
    date = models.DateField('Date', auto_now_add=True, db_index=True)
    
    # Totals
    total_users = models.IntegerField('Total Users', default=0)
    total_quizzes = models.IntegerField('Total Quizzes', default=0)
    total_attempts = models.IntegerField('Total Attempts', default=0)
    
    # Health
    avg_response_time_ms = models.FloatField('Avg Response Time (ms)', default=0.0)
    error_rate = models.FloatField('Error Rate %', default=0.0)
    uptime_percentage = models.FloatField('Uptime %', default=99.9)
    
    # Growth
    daily_active_users = models.IntegerField('DAU', default=0)
    weekly_active_users = models.IntegerField('WAU', default=0)
    monthly_active_users = models.IntegerField('MAU', default=0)
    
    # Engagement
    avg_sessions_per_user = models.FloatField('Avg Sessions/User', default=0.0)
    avg_session_duration = models.IntegerField('Avg Session (s)', default=0)
    
    # Performance
    most_attempted_quiz = models.CharField('Most Attempted Quiz', max_length=255, blank=True)
    most_attempted_category = models.CharField('Most Attempted Category', max_length=255, blank=True)
    
    class Meta:
        db_table = 'analytics_platformmetrics'
        verbose_name = 'Platform Metrics'
        verbose_name_plural = 'Platform Metrics'
        ordering = ['-date']
    
    def __str__(self):
        return f"Platform: {self.date} (DAU: {self.daily_active_users})"


class CollegeAnalytics(models.Model):
    """College-specific analytics."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    college = models.ForeignKey('accounts.College', on_delete=models.CASCADE, related_name='analytics')
    
    # Date
    date = models.DateField('Date', auto_now_add=True, db_index=True)
    
    # Metrics
    total_students = models.IntegerField('Total Students', default=0)
    active_students = models.IntegerField('Active Students', default=0)
    total_quizzes_attempted = models.IntegerField('Quizzes Attempted', default=0)
    avg_accuracy = models.FloatField('Avg Accuracy %', default=0.0)
    total_xp = models.IntegerField('Total XP', default=0)
    avg_xp_per_student = models.FloatField('Avg XP/Student', default=0.0)
    
    # Ranking
    rank = models.IntegerField('Rank', null=True, blank=True)
    
    class Meta:
        db_table = 'analytics_collegeanalytics'
        verbose_name = 'College Analytics'
        verbose_name_plural = 'College Analytics'
        ordering = ['-date']
        unique_together = ('college', 'date')
    
    def __str__(self):
        return f"{self.college.name}: {self.date}"
