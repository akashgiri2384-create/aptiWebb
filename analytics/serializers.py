"""DRF serializers for analytics - PLACEHOLDER"""
from rest_framework import serializers
from .models import AnalyticsSnapshot, UserReport, PlatformMetrics

class AnalyticsSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsSnapshot
        fields = ['date', 'total_users', 'active_users', 'total_attempts', 'avg_accuracy']

class UserReportSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    class Meta:
        model = UserReport
        fields = ['report_type', 'type_display', 'period_start', 'period_end', 
                  'quizzes_attempted', 'quizzes_passed', 'avg_accuracy', 'total_xp_earned']

class PlatformMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformMetrics
        fields = ['date', 'total_users', 'daily_active_users', 'weekly_active_users', 
                  'monthly_active_users', 'uptime_percentage']
