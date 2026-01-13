"""Django admin for analytics"""
from django.contrib import admin
from .models import AnalyticsSnapshot, UserReport, PlatformMetrics, CollegeAnalytics

@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_users', 'active_users', 'total_attempts', 'avg_accuracy']
    list_filter = ['date']
    readonly_fields = ['date', 'total_users', 'active_users']
    
    def has_add_permission(self, request):
        return False

@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'report_type', 'period_start', 'quizzes_attempted', 'avg_accuracy', 'is_sent']
    list_filter = ['report_type', 'is_sent', 'period_start']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'sent_at']

@admin.register(PlatformMetrics)
class PlatformMetricsAdmin(admin.ModelAdmin):
    list_display = ['date', 'daily_active_users', 'weekly_active_users', 'uptime_percentage']
    list_filter = ['date']
    readonly_fields = ['date']

@admin.register(CollegeAnalytics)
class CollegeAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['college', 'date', 'total_students', 'active_students', 'avg_accuracy', 'rank']
    list_filter = ['date']
    search_fields = ['college__name']
