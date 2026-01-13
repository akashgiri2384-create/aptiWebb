"""
Django admin configuration for daily quizzes app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import DailyQuiz, RewardedVideoAd, AdView, DailyQuizUnlock, KeyLedger


@admin.register(DailyQuiz)
class DailyQuizAdmin(admin.ModelAdmin):
    """Admin interface for DailyQuiz."""
    
    list_display = [
        'date', 'slot_display', 'quiz_title', 'difficulty',
        'keys_required', 'xp_multiplier', 'is_active'
    ]
    list_filter = ['slot', 'difficulty', 'is_active', 'date']
    search_fields = ['quiz_title']
    ordering = ['-date', 'slot']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Quiz Details', {
            'fields': ('quiz', 'quiz_title', 'difficulty')
        }),
        ('Scheduling', {
            'fields': ('date', 'slot')
        }),
        ('Requirements & Rewards', {
            'fields': ('keys_required', 'xp_multiplier')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def slot_display(self, obj):
        """Display slot with icon."""
        icons = {'morning': '🌅', 'evening': '🌆'}
        icon = icons.get(obj.slot, '')
        return f"{icon} {obj.get_slot_display()}"
    slot_display.short_description = 'Slot'


@admin.register(RewardedVideoAd)
class RewardedVideoAdAdmin(admin.ModelAdmin):
    """Admin interface for RewardedVideoAd."""
    
    list_display = [
        'title', 'ad_network', 'reward_keys', 'reward_xp',
        'completion_rate_display', 'priority', 'is_active'
    ]
    list_filter = ['ad_network', 'is_active']
    search_fields = ['title', 'network_id']
    ordering = ['-is_active', '-priority', '-created_at']
    
    fieldsets = (
        ('Ad Configuration', {
            'fields': ('title', 'ad_network', 'network_id')
        }),
        ('Rewards', {
            'fields': ('reward_keys', 'reward_xp', 'min_watch_duration_seconds')
        }),
        ('Status & Priority', {
            'fields': ('is_active', 'priority')
        }),
        ('Performance Metrics', {
            'fields': ('total_views', 'total_completions', 'total_skips', 'completion_rate')
        }),
    )
    readonly_fields = ['total_views', 'total_completions', 'total_skips', 'completion_rate']
    
    def completion_rate_display(self, obj):
        """Display completion rate with color."""
        rate = obj.completion_rate
        if rate >= 80:
            color = 'green'
        elif rate >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            rate
        )
    completion_rate_display.short_description = 'Completion Rate'


@admin.register(AdView)
class AdViewAdmin(admin.ModelAdmin):
    """Admin interface for AdView."""
    
    list_display = [
        'user_display', 'ad_title', 'status_display',
        'watch_duration_seconds', 'fraud_display', 'created_at'
    ]
    list_filter = ['status', 'is_flagged_fraud', 'created_at']
    search_fields = ['user__email', 'ad__title', 'ip_address']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    readonly_fields = [
        'user', 'ad', 'daily_quiz', 'status', 'watch_duration_seconds',
        'device_fingerprint', 'ip_address', 'user_agent',
        'is_flagged_fraud', 'fraud_reason', 'created_at', 'completed_at'
    ]
    
    fieldsets = (
        ('References', {
            'fields': ('user', 'ad', 'daily_quiz')
        }),
        ('Tracking', {
            'fields': ('status', 'watch_duration_seconds', 'created_at', 'completed_at')
        }),
        ('Fraud Detection', {
            'fields': ('device_fingerprint', 'ip_address', 'user_agent',
                      'is_flagged_fraud', 'fraud_reason')
        }),
    )
    
    def user_display(self, obj):
        """Display user email."""
        return obj.user.email
    user_display.short_description = 'User'
    
    def ad_title(self, obj):
        """Display ad title."""
        return obj.ad.title
    ad_title.short_description = 'Ad'
    
    def status_display(self, obj):
        """Display status with color."""
        colors = {
            'started': 'blue',
            'completed': 'green',
            'skipped': 'orange',
            'fraudulent': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def fraud_display(self, obj):
        """Display fraud status."""
        if obj.is_flagged_fraud:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ FRAUD</span><br><small>{}</small>',
                obj.fraud_reason
            )
        return format_html('<span style="color: green;">✓ Valid</span>')
    fraud_display.short_description = 'Fraud Status'


@admin.register(DailyQuizUnlock)
class DailyQuizUnlockAdmin(admin.ModelAdmin):
    """Admin interface for DailyQuizUnlock."""
    
    list_display = [
        'user_display', 'quiz_display', 'progress_display',
        'status_display', 'created_at'
    ]
    list_filter = ['is_unlocked', 'is_completed', 'created_at']
    search_fields = ['user__email', 'daily_quiz__quiz_title']
    ordering = ['-created_at']
    readonly_fields = [
        'user', 'daily_quiz', 'keys_earned', 'keys_required',
        'is_unlocked', 'is_completed', 'unlocked_at',
        'expires_at', 'completed_at', 'created_at'
    ]
    
    fieldsets = (
        ('References', {
            'fields': ('user', 'daily_quiz')
        }),
        ('Keys Progress', {
            'fields': ('keys_earned', 'keys_required')
        }),
        ('Status', {
            'fields': ('is_unlocked', 'is_completed')
        }),
        ('Timestamps', {
            'fields': ('unlocked_at', 'expires_at', 'completed_at', 'created_at')
        }),
    )
    
    def user_display(self, obj):
        """Display user email."""
        return obj.user.email
    user_display.short_description = 'User'
    
    def quiz_display(self, obj):
        """Display quiz title."""
        return obj.daily_quiz.quiz_title
    quiz_display.short_description = 'Quiz'
    
    def progress_display(self, obj):
        """Display progress bar."""
        if obj.keys_required > 0:
            val = (obj.keys_earned / obj.keys_required) * 100
        else:
            val = 0
            
        return format_html(
            '{}/{} keys ({:.0f}%)',
            obj.keys_earned,
            obj.keys_required,
            val
        )
    progress_display.short_description = 'Progress'
    
    def status_display(self, obj):
        """Display status badges."""
        from django.utils.safestring import mark_safe
        badges = []
        if obj.is_unlocked:
            badges.append('<span style="color: green;">🔓 Unlocked</span>')
        else:
            badges.append('<span style="color: orange;">🔒 Locked</span>')
        
        if obj.is_completed:
            badges.append('<span style="color: blue;">✓ Completed</span>')
        
        return format_html('{}', mark_safe(' '.join(badges)))
    status_display.short_description = 'Status'


@admin.register(KeyLedger)
class KeyLedgerAdmin(admin.ModelAdmin):
    """Admin interface for KeyLedger."""
    
    list_display = [
        'user_display', 'transaction_type_display', 'amount_display',
        'balance_after', 'description', 'created_at'
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__email', 'description']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    readonly_fields = [
        'user', 'transaction_type', 'amount', 'balance_after',
        'description', 'ad_view', 'unlock', 'created_at'
    ]
    
    fieldsets = (
        ('Transaction', {
            'fields': ('user', 'transaction_type', 'amount', 'balance_after', 'description')
        }),
        ('References', {
            'fields': ('ad_view', 'unlock')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def user_display(self, obj):
        """Display user email."""
        return obj.user.email
    user_display.short_description = 'User'
    
    def transaction_type_display(self, obj):
        """Display transaction type with color."""
        colors = {
            'earned_ad': 'green',
            'earned_quiz': 'green',
            'used_unlock': 'blue',
            'expired': 'red',
            'admin_grant': 'purple',
            'admin_revoke': 'orange',
        }
        color = colors.get(obj.transaction_type, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_transaction_type_display()
        )
    transaction_type_display.short_description = 'Type'
    
    def amount_display(self, obj):
        """Display amount with color."""
        if obj.amount > 0:
            return format_html('<span style="color: green; font-weight: bold;">+{}</span>', obj.amount)
        else:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', obj.amount)
    amount_display.short_description = 'Amount'
