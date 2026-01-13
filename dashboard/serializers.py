"""
DRF serializers for dashboard app.
"""

from rest_framework import serializers
from .models import UserActivityLog, DailyActivityMetric


class UserActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for UserActivityLog."""
    
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    
    class Meta:
        model = UserActivityLog
        fields = [
            'id', 'activity_type', 'activity_type_display', 'description',
            'xp_change', 'key_change', 'rank_change', 'created_at'
        ]
        read_only_fields = fields


class DailyActivityMetricSerializer(serializers.ModelSerializer):
    """Serializer for DailyActivityMetric."""
    
    class Meta:
        model = DailyActivityMetric
        fields = [
            'date', 'quizzes_attempted', 'questions_answered',
            'correct_answers', 'wrong_answers', 'accuracy_percentage',
            'xp_earned', 'xp_spent', 'keys_earned', 'keys_used',
            'total_time_minutes', 'badges_earned'
        ]
        read_only_fields = fields
