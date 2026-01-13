"""
Django admin configuration for dashboard app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import UserActivityLog, DailyActivityMetric


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    """Admin interface for UserActivityLog."""
    
    list_display = [
        'user_display', 'activity_type_display', 'description',
        'xp_display', 'key_display', 'created_at'
    ]
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__email', 'description']
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'user', 'activity_type', 'description',
        'quiz_id', 'xp_change', 'key_change', 'rank_change',
        'badge_id', 'metadata', 'created_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Activity', {
            'fields': ('id', 'user', 'activity_type', 'description')
        }),
        ('Changes', {
            'fields': ('xp_change', 'key_change', 'rank_change')
        }),
        ('Related Data', {
            'fields': ('quiz_id', 'badge_id', 'metadata')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def user_display(self, obj):
        """Display user email."""
        return obj.user.email
    user_display.short_description = 'User'
    
    def activity_type_display(self, obj):
        """Display activity type with color."""
        colors = {
            'quiz_passed': 'green',
            'quiz_failed': 'red',
            'xp_earned': 'blue',
            'key_earned': 'purple',
            'badge_unlocked': 'orange',
        }
        color = colors.get(obj.activity_type, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_activity_type_display()
        )
    activity_type_display.short_description = 'Activity Type'
    
    def xp_display(self, obj):
        """Display XP change with color."""
        if obj.xp_change > 0:
            return format_html('<span style="color: green;">+{}</span>', obj.xp_change)
        elif obj.xp_change < 0:
            return format_html('<span style="color: red;">{}</span>', obj.xp_change)
        return '-'
    xp_display.short_description = 'XP'
    
    def key_display(self, obj):
        """Display key change with color."""
        if obj.key_change > 0:
            return format_html('<span style="color: green;">+{}</span>', obj.key_change)
        elif obj.key_change < 0:
            return format_html('<span style="color: red;">{}</span>', obj.key_change)
        return '-'
    key_display.short_description = 'Keys'


@admin.register(DailyActivityMetric)
class DailyActivityMetricAdmin(admin.ModelAdmin):
    """Admin interface for DailyActivityMetric."""
    
    list_display = [
        'user_display', 'date', 'quizzes_attempted',
        'accuracy_display', 'xp_earned', 'keys_earned'
    ]
    list_filter = ['date']
    search_fields = ['user__email']
    ordering = ['-date']
    readonly_fields = [
        'id', 'user', 'date', 'quizzes_attempted',
        'questions_answered', 'correct_answers', 'wrong_answers',
        'accuracy_percentage', 'xp_earned', 'xp_spent',
        'keys_earned', 'keys_used', 'total_time_minutes',
        'badges_earned', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'date'
    
    fieldsets = (
        ('User & Date', {
            'fields': ('id', 'user', 'date')
        }),
        ('Quiz Metrics', {
            'fields': ('quizzes_attempted', 'questions_answered',
                      'correct_answers', 'wrong_answers', 'accuracy_percentage')
        }),
        ('XP & Keys', {
            'fields': ('xp_earned', 'xp_spent', 'keys_earned', 'keys_used')
        }),
        ('Other Metrics', {
            'fields': ('total_time_minutes', 'badges_earned')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def user_display(self, obj):
        """Display user email."""
        return obj.user.email
    user_display.short_description = 'User'
    
    def accuracy_display(self, obj):
        """Display accuracy with color."""
        accuracy = obj.accuracy_percentage
        if accuracy >= 80:
            color = 'green'
        elif accuracy >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            accuracy
        )
    accuracy_display.short_description = 'Accuracy'
