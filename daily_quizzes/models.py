"""
Daily quiz models with lock/key system and fraud detection.

Models:
- DailyQuiz: Daily quiz configuration (2 per day)
- RewardedVideoAd: Video ad configuration
- AdView: Individual ad views with fraud detection
- DailyQuizUnlock: Per-user unlock status
- KeyLedger: Complete key transaction history
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import uuid

User = get_user_model()


class DailyQuiz(models.Model):
    """
    Daily quiz configuration.
    
    Two quizzes per day (morning and evening) that require keys to unlock.
    """
    
    SLOT_CHOICES = [
        ('morning', 'Morning (8 AM)'),
        ('evening', 'Evening (6 PM)'),
        ('night', 'Night (10 PM)')
    ]
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Quiz assignment
    quiz = models.ForeignKey(
        'quizzes.Quiz',
        on_delete=models.CASCADE,
        related_name='daily_assignments',
        null=True, blank=True
    )
    quiz_title = models.CharField('Quiz Title', max_length=255, blank=True)  # Legacy/Backup
    
    # Scheduling
    date = models.DateField('Date', db_index=True)
    slot = models.CharField('Slot', max_length=10, choices=SLOT_CHOICES)
    
    # Requirements
    keys_required = models.IntegerField('Keys Required', default=0)
    xp_multiplier = models.FloatField('XP Multiplier', default=5.0)
    
    # Metadata
    difficulty = models.CharField('Difficulty', max_length=10, choices=DIFFICULTY_CHOICES)
    is_active = models.BooleanField('Active', default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_quizzes_dailyquiz'
        verbose_name = 'Daily Quiz'
        verbose_name_plural = 'Daily Quizzes'
        unique_together = ('date', 'slot')
        ordering = ['-date', 'slot']
        indexes = [
            models.Index(fields=['date', 'is_active']),
            models.Index(fields=['date', 'slot']),
        ]
    
    def __str__(self):
        return f"Daily Quiz {self.date} ({self.get_slot_display()})"


class RewardedVideoAd(models.Model):
    """
    Video ad configuration and tracking.
    
    Manages ad network integration and performance metrics.
    """
    
    AD_NETWORK_CHOICES = [
        ('admob', 'Google AdMob'),
        ('custom', 'Custom Network')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Ad configuration
    title = models.CharField('Title', max_length=255)
    ad_network = models.CharField('Ad Network', max_length=20, choices=AD_NETWORK_CHOICES)
    network_id = models.CharField('Network Ad Unit ID', max_length=255)
    
    # Reward configuration
    reward_keys = models.IntegerField('Reward Keys', default=1)
    reward_xp = models.IntegerField('Reward XP', default=10)
    
    # Duration requirements
    min_watch_duration_seconds = models.IntegerField('Min Watch Duration (seconds)', default=30)
    
    # Status
    is_active = models.BooleanField('Active', default=True, db_index=True)
    priority = models.IntegerField('Priority', default=0, help_text='Higher number = higher priority')
    
    # Performance metrics (denormalized)
    total_views = models.IntegerField('Total Views', default=0)
    total_completions = models.IntegerField('Total Completions', default=0)
    total_skips = models.IntegerField('Total Skips', default=0)
    completion_rate = models.FloatField('Completion Rate %', default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_quizzes_rewardedvideoad'
        verbose_name = 'Rewarded Video Ad'
        verbose_name_plural = 'Rewarded Video Ads'
        ordering = ['-is_active', '-priority', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'priority']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.completion_rate:.1f}%)"
    
    def update_completion_rate(self):
        """Recalculate completion rate."""
        if self.total_views == 0:
            self.completion_rate = 0.0
        else:
            self.completion_rate = (self.total_completions / self.total_views) * 100
        self.save(update_fields=['completion_rate'])


class AdView(models.Model):
    """
    Individual ad view tracking with fraud detection.
    
    Tracks each ad view with device fingerprinting and fraud detection.
    """
    
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('skipped', 'Skipped'),
        ('completed', 'Completed'),
        ('fraudulent', 'Fraudulent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # References
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ad_views'
    )
    ad = models.ForeignKey(
        RewardedVideoAd,
        on_delete=models.CASCADE,
        related_name='views',
        null=True,
        blank=True
    )
    daily_quiz = models.ForeignKey(
        DailyQuiz,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ad_views'
    )
    
    # Tracking
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, db_index=True)
    watch_duration_seconds = models.IntegerField('Watch Duration (seconds)', default=0)
    
    # Fraud detection
    device_fingerprint = models.CharField('Device Fingerprint', max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField('IP Address', null=True, blank=True)
    user_agent = models.TextField('User Agent', null=True, blank=True)
    is_flagged_fraud = models.BooleanField('Flagged as Fraud', default=False, db_index=True)
    fraud_reason = models.CharField('Fraud Reason', max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField('Completed At', null=True, blank=True)
    
    class Meta:
        db_table = 'daily_quizzes_adview'
        verbose_name = 'Ad View'
        verbose_name_plural = 'Ad Views'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status', '-created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['is_flagged_fraud']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.ad.title} ({self.get_status_display()})"


class DailyQuizUnlock(models.Model):
    """
    Per-user daily quiz unlock status.
    
    Tracks unlock progress and expiry for each user and daily quiz.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='daily_quiz_unlocks'
    )
    daily_quiz = models.ForeignKey(
        DailyQuiz,
        on_delete=models.CASCADE,
        related_name='unlocks'
    )
    
    # Keys tracking
    keys_earned = models.IntegerField('Keys Earned', default=0)
    keys_required = models.IntegerField('Keys Required', default=5)
    
    # Status
    is_unlocked = models.BooleanField('Unlocked', default=False, db_index=True)
    is_completed = models.BooleanField('Completed', default=False)
    
    # Timestamps
    unlocked_at = models.DateTimeField('Unlocked At', null=True, blank=True)
    expires_at = models.DateTimeField('Expires At', null=True, blank=True)  # 24 hour expiry
    completed_at = models.DateTimeField('Completed At', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_quizzes_dailyquizunlock'
        verbose_name = 'Daily Quiz Unlock'
        verbose_name_plural = 'Daily Quiz Unlocks'
        unique_together = ('user', 'daily_quiz')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_unlocked']),
            models.Index(fields=['user', 'daily_quiz']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.daily_quiz}"
    
    def is_expired(self):
        """Check if unlock has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at


class KeyLedger(models.Model):
    """
    Complete key transaction history.
    
    Maintains running balance and full audit trail of all key transactions.
    """
    
    TRANSACTION_TYPES = [
        ('earned_ad', 'Earned from Ad'),
        ('earned_quiz', 'Earned from Quiz'),
        ('used_unlock', 'Used for Unlock'),
        ('expired', 'Expired'),
        ('admin_grant', 'Admin Grant'),
        ('admin_revoke', 'Admin Revoke'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='key_transactions'
    )
    
    # Transaction details
    transaction_type = models.CharField(
        'Transaction Type',
        max_length=20,
        choices=TRANSACTION_TYPES,
        db_index=True
    )
    amount = models.IntegerField('Amount')  # Positive or negative
    balance_after = models.IntegerField('Balance After')  # Running balance
    description = models.CharField('Description', max_length=255)
    
    # References
    ad_view = models.ForeignKey(
        AdView,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='key_transactions'
    )
    unlock = models.ForeignKey(
        DailyQuizUnlock,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='key_transactions'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'daily_quizzes_keyledger'
        verbose_name = 'Key Ledger Entry'
        verbose_name_plural = 'Key Ledger'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
        ]
    
    def __str__(self):
        sign = '+' if self.amount >= 0 else ''
        return f"{self.user.email} - {sign}{self.amount} keys ({self.get_transaction_type_display()})"
