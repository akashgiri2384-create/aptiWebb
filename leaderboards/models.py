"""
Leaderboard models.

Models:
- LeaderboardEntry: Ranking entries with multiple scopes (quiz/overall/college)
- RankSnapshot: Historical snapshots for trend analysis
"""

from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class LeaderboardEntry(models.Model):
    """
    Leaderboard ranking entries with multiple scopes.
    
    Supports 3 scopes:
    - quiz: Per-quiz top scorers
    - overall: Student rankings by XP
    - college: College rankings by aggregate XP
    
    Supports 3 periods:
    - all_time: All-time rankings
    - weekly: Weekly rankings
    - monthly: Monthly rankings
    """
    
    SCOPE_CHOICES = [
        ('overall', 'Overall Student'),
        ('quiz', 'Per-Quiz'),
        ('college', 'College'),
    ]
    
    PERIOD_CHOICES = [
        ('all_time', 'All Time'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Leaderboard scope
    scope = models.CharField('Scope', max_length=20, choices=SCOPE_CHOICES, db_index=True)
    period = models.CharField('Period', max_length=20, choices=PERIOD_CHOICES, db_index=True)
    
    # Reference data (contextual based on scope)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='leaderboard_entries',
        help_text='For overall/quiz scopes'
    )
    quiz = models.ForeignKey(
        'quizzes.Quiz',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='leaderboard_entries',
        help_text='For quiz scope only'
    )
    college = models.ForeignKey(
        'accounts.College',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='leaderboard_entries',
        help_text='For college scope only'
    )
    
    # Ranking data
    rank = models.IntegerField('Rank', db_index=True, help_text='1, 2, 3, etc.')
    score = models.FloatField('Score', help_text='XP for overall/college, percentage for quiz')
    
    # Period tracking
    period_start = models.DateField('Period Start', db_index=True)
    period_end = models.DateField('Period End')
    
    # Metadata
    tie_count = models.IntegerField('Tie Count', default=0, help_text='Number of users with same score')
    percentile = models.FloatField('Percentile', default=0.0, help_text='0-100, higher is better')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'leaderboards_leaderboardentry'
        verbose_name = 'Leaderboard Entry'
        verbose_name_plural = 'Leaderboard Entries'
        ordering = ['scope', 'period', 'rank']
        unique_together = ('scope', 'period', 'user', 'quiz', 'college', 'period_start')
        indexes = [
            models.Index(fields=['scope', 'period', 'rank']),
            models.Index(fields=['user', 'scope']),
            models.Index(fields=['period_start', 'period']),
            models.Index(fields=['score', '-rank']),
        ]
    
    def __str__(self):
        if self.scope == 'overall' and self.user:
            return f"{self.user.email} - Rank #{self.rank} (Overall {self.period})"
        elif self.scope == 'quiz' and self.user and self.quiz:
            return f"{self.user.email} - Rank #{self.rank} ({self.quiz.title})"
        elif self.scope == 'college' and self.college:
            return f"{self.college.name} - Rank #{self.rank} (College {self.period})"
        return f"Rank #{self.rank} ({self.scope})"


class RankSnapshot(models.Model):
    """
    Historical snapshots of rankings for trend analysis.
    
    Created daily to track rank changes over time.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Reference
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rank_snapshots'
    )
    
    # Scope
    scope = models.CharField('Scope', max_length=20, db_index=True)
    period = models.CharField('Period', max_length=20)
    
    # Rank at snapshot time
    rank_at_snapshot = models.IntegerField('Rank')
    score_at_snapshot = models.FloatField('Score')
    percentile_at_snapshot = models.FloatField('Percentile')
    
    # Timestamp
    snapshot_date = models.DateField('Snapshot Date', auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'leaderboards_ranksnapshot'
        verbose_name = 'Rank Snapshot'
        verbose_name_plural = 'Rank Snapshots'
        ordering = ['-snapshot_date']
        indexes = [
            models.Index(fields=['user', 'scope', '-snapshot_date']),
            models.Index(fields=['snapshot_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - Rank {self.rank_at_snapshot} on {self.snapshot_date} ({self.scope})"
