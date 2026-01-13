"""
XP and reward system models.

COMPLETE IMPLEMENTATION - All 5 models production-ready.

Models:
- XPLog: Transaction history of all XP changes
- XPConfig: Configurable XP rules and multipliers
- UserStats: Denormalized XP statistics for performance
- Badge: Achievement badge definitions
- UserBadge: User's earned badges
"""

from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class XPLog(models.Model):
    """Complete transaction history of XP changes."""
    
    TRANSACTION_TYPES = [
        ('earned_quiz', 'Earned from Quiz'),
        ('earned_daily', 'Earned from Daily Quiz'),
        ('earned_streak', 'Earned from Streak'),
        ('earned_accuracy', 'Earned from Accuracy'),
        ('earned_speed', 'Earned from Speed Bonus'),
        ('earned_first_attempt', 'Earned from First Attempt'),
        ('earned_badge', 'Earned from Badge'),
        ('spent_feature', 'Spent on Feature'),
        ('decayed', 'Decayed (Monthly Inactivity)'),
        ('admin_grant', 'Admin Grant'),
        ('admin_revoke', 'Admin Revoke'),
        ('refund', 'Refund'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='xp_transactions')
    
    # Transaction details
    transaction_type = models.CharField('Type', max_length=50, choices=TRANSACTION_TYPES, db_index=True)
    amount = models.IntegerField('Amount', help_text='Positive or negative')
    balance_after = models.IntegerField('Balance After', help_text='Running balance')
    description = models.CharField('Description', max_length=255)
    
    # References
    quiz_attempt = models.ForeignKey(
        'quizzes.QuizAttempt',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='xp_logs'
    )
    daily_quiz_unlock = models.ForeignKey(
        'daily_quizzes.DailyQuizUnlock',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='xp_logs'
    )
    badge = models.ForeignKey(
        'xp_system.Badge',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='xp_logs'
    )
    
    # Metadata (flexible JSON for breakdown)
    metadata = models.JSONField('Metadata', default=dict, blank=True,
                                help_text='Additional data like difficulty, accuracy, bonuses')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'xp_system_xplog'
        verbose_name = 'XP Log Entry'
        verbose_name_plural = 'XP Log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
        ]
    
    def __str__(self):
        sign = '+' if self.amount >= 0 else ''
        return f"{self.user.email} - {sign}{self.amount} XP ({self.get_transaction_type_display()})"


class XPConfig(models.Model):
    """Configurable XP rules and multipliers."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Base XP values per difficulty
    xp_easy_correct = models.IntegerField('Easy - Correct Answer XP', default=10)
    xp_medium_correct = models.IntegerField('Medium - Correct Answer XP', default=25)
    xp_hard_correct = models.IntegerField('Hard - Correct Answer XP', default=50)
    
    xp_easy_wrong = models.IntegerField('Easy - Wrong Answer XP', default=0)
    xp_medium_wrong = models.IntegerField('Medium - Wrong Answer XP', default=0)
    xp_hard_wrong = models.IntegerField('Hard - Wrong Answer XP', default=0)
    
    # Multipliers
    daily_quiz_multiplier = models.FloatField('Daily Quiz Multiplier', default=5.0,
                                              help_text='5x XP for daily quizzes')
    
    # Bonuses
    accuracy_100_bonus = models.IntegerField('100% Accuracy Bonus', default=10)
    accuracy_90_bonus = models.IntegerField('90%+ Accuracy Bonus', default=5)
    first_attempt_bonus = models.IntegerField('First Attempt Pass Bonus', default=25)
    speed_bonus = models.IntegerField('Speed Bonus', default=10,
                                     help_text='Bonus if completed in 75% of time')
    
    # Streak bonuses
    streak_3_bonus = models.IntegerField('3-Day Streak Bonus', default=50)
    streak_7_bonus = models.IntegerField('7-Day Streak Bonus', default=100)
    streak_30_bonus = models.IntegerField('30-Day Streak Bonus', default=500)
    
    # Levels
    xp_per_level = models.IntegerField('XP per Level', default=1000)
    max_level = models.IntegerField('Maximum Level', default=100)
    
    # Decay
    monthly_decay_percentage = models.IntegerField('Monthly Decay % (Inactive)', default=5,
                                                   help_text='Inactive users lose this % per month')
    
    # Status
    is_active = models.BooleanField('Active', default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'xp_system_xpconfig'
        verbose_name = 'XP Configuration'
        verbose_name_plural = 'XP Configuration'
    
    def __str__(self):
        return f"XP Config (updated {self.updated_at.strftime('%Y-%m-%d')})"


class UserStats(models.Model):
    """Denormalized XP statistics for performance."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='xp_stats')
    
    # Totals
    total_xp = models.IntegerField('Total XP', default=0)
    season_xp = models.IntegerField('Season XP', default=0, help_text='XP earned in current season (for Ranks)')
    total_xp_earned = models.IntegerField('Total XP Earned', default=0)
    total_xp_spent = models.IntegerField('Total XP Spent', default=0)

    # Levels
    level = models.IntegerField('Level', default=1)
    xp_in_current_level = models.IntegerField('XP in Current Level', default=0)
    xp_needed_for_next_level = models.IntegerField('XP Needed for Next Level', default=1000)

    # Streaks
    current_streak = models.IntegerField('Current Streak (days)', default=0)
    longest_streak = models.IntegerField('Longest Streak (days)', default=0)
    last_activity_date = models.DateField('Last Activity Date', null=True, blank=True)
    
    # Milestones
    quizzes_passed = models.IntegerField('Quizzes Passed', default=0)
    quizzes_attempted = models.IntegerField('Quizzes Attempted', default=0)
    total_accuracy = models.FloatField('Overall Accuracy %', default=0.0)
    
    # Badges
    badges_earned = models.IntegerField('Badges Earned', default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_decay_date = models.DateField('Last Decay Date', null=True, blank=True)
    
    class Meta:
        db_table = 'xp_system_userstats'
        verbose_name = 'User XP Stats'
        verbose_name_plural = 'User XP Stats'
    
    def __str__(self):
        return f"{self.user.email} - Level {self.level} ({self.total_xp} XP)"


class Badge(models.Model):
    """Achievement badge definitions."""
    
    RARITY_CHOICES = [
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
        ('rank', 'Rank'), # New Rarity for Ranks
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic info
    name = models.CharField('Name', max_length=100, unique=True)
    description = models.TextField('Description')
    icon = models.CharField('Icon Name', max_length=50, help_text='Icon class name', blank=True, null=True)
    emoji = models.CharField('Emoji', max_length=10, blank=True)
    
    # Rank System Fields
    rank_order = models.IntegerField('Rank Order', default=0, help_text='1-80 for Ranks')
    xp_threshold = models.IntegerField('XP Threshold', default=0, help_text='Season XP needed to unlock')
    image_path = models.CharField('Image Path', max_length=255, blank=True, null=True, help_text='Path in static/images/badges/')

    # Rarity
    rarity = models.CharField('Rarity', max_length=20, choices=RARITY_CHOICES, default='common')
    
    # Unlock criteria (Legacy / Achievements)
    unlock_type = models.CharField('Unlock Type', max_length=50,
                                   help_text='e.g., first_quiz, quiz_master, accuracy_hero', blank=True, null=True)
    unlock_requirement = models.JSONField('Unlock Requirement', default=dict, blank=True,
                                         help_text='e.g., {"quizzes_passed": 10}')
    
    # Reward
    xp_reward = models.IntegerField('XP Reward', default=0,
                                   help_text='XP bonus awarded on unlock')
    
    # Status
    is_active = models.BooleanField('Active', default=True, db_index=True)
    
    # Stats
    users_unlocked = models.IntegerField('Users Unlocked', default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'xp_system_badge'
        verbose_name = 'Badge'
        verbose_name_plural = 'Badges'
        ordering = ['rank_order', 'rarity', 'name'] # Order by rank first
        indexes = [
            models.Index(fields=['unlock_type', 'is_active']),
            models.Index(fields=['rank_order']),
        ]
    
    def __str__(self):
        return f"{self.emoji} {self.name} ({self.get_rarity_display()})"


class UserBadge(models.Model):
    """User's earned badges."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')
    
    # Unlock info
    unlocked_at = models.DateTimeField('Unlocked At', auto_now_add=True)
    
    class Meta:
        db_table = 'xp_system_userbadge'
        verbose_name = 'User Badge'
        verbose_name_plural = 'User Badges'
        unique_together = ('user', 'badge')
        ordering = ['-unlocked_at']
        indexes = [
            models.Index(fields=['user', 'badge']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.badge.name}"
