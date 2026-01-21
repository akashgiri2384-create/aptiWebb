"""Django admin for xp_system"""
from django.contrib import admin
from django.utils.html import format_html
from .models import XPLog, XPConfig, UserStats, Badge, UserBadge

@admin.register(XPLog)
class XPLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount_display', 'transaction_type', 'balance_after', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__email', 'description']
    readonly_fields = ['user', 'amount', 'balance_after', 'created_at']
    
    def amount_display(self, obj):
        if obj.amount > 0:
            return format_html('<span style="color: green;">+{}</span>', obj.amount)
        return format_html('<span style="color: red;">{}</span>', obj.amount)
    amount_display.short_description = 'Amount'

@admin.register(XPConfig)
class XPConfigAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'xp_per_level', 'max_level', 'is_active']
    fieldsets = (
        ('Base XP', {'fields': ('xp_easy_correct', 'xp_medium_correct', 'xp_hard_correct')}),
        ('Bonuses', {'fields': ('accuracy_100_bonus', 'accuracy_90_bonus', 'speed_bonus', 'first_attempt_bonus')}),
        ('Streaks', {'fields': ('streak_3_bonus', 'streak_7_bonus', 'streak_30_bonus')}),
        ('Levels', {'fields': ('xp_per_level', 'max_level')}),
    )

@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'total_xp', 'current_streak', 'badges_earned']
    search_fields = ['user__email']
    readonly_fields = ['user', 'level']

    def save_model(self, request, obj, form, change):
        if change and 'total_xp' in form.changed_data:
            # Recalculate level based on new XP
            from .services import XPService
            obj.level = XPService.calculate_level(obj.total_xp)
            
            # Invalidate leaderboard cache
            from leaderboards.services import LeaderboardService
            LeaderboardService.invalidate_leaderboard_cache()
            
        super().save_model(request, obj, form, change)

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['emoji_display', 'name', 'rarity', 'unlock_type', 'xp_reward', 'users_unlocked', 'is_active']
    list_filter = ['rarity', 'unlock_type', 'is_active']
    search_fields = ['name']
    
    def emoji_display(self, obj):
        return obj.emoji if obj.emoji else '🏅'
    emoji_display.short_description = 'Badge'

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'unlocked_at']
    list_filter = ['unlocked_at']
    search_fields = ['user__email', 'badge__name']
