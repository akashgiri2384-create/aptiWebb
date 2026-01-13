"""Django admin configuration for leaderboards app"""
from django.contrib import admin
from django.utils.html import format_html
from .models import LeaderboardEntry, RankSnapshot

@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = ['rank_display', 'user_display', 'scope', 'period', 'score', 'percentile', 'updated_at']
    list_filter = ['scope', 'period', 'period_start']
    search_fields = ['user__email', 'college__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['scope', 'period', 'rank']
    
    def rank_display(self, obj):
        if obj.rank <= 3:
            medals = {1: '🥇', 2: '🥈', 3: '🥉'}
            return format_html('<span style="font-size: 20px;">{} {}</span>', medals[obj.rank], obj.rank)
        return f"#{obj.rank}"
    rank_display.short_description = 'Rank'
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.email
        elif obj.college:
            return obj.college.name
        return 'N/A'
    user_display.short_description = 'User/College'

@admin.register(RankSnapshot)
class RankSnapshotAdmin(admin.ModelAdmin):
    list_display = ['user', 'scope', 'rank_at_snapshot', 'score_at_snapshot', 'snapshot_date']
    list_filter = ['scope', 'snapshot_date']
    search_fields = ['user__email']
    readonly_fields = ['snapshot_date']
    ordering = ['-snapshot_date']
