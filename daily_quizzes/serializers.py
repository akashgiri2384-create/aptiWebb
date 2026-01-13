"""
DRF serializers for daily quizzes app.
"""

from rest_framework import serializers
from .models import DailyQuiz, RewardedVideoAd, AdView, DailyQuizUnlock, KeyLedger


class DailyQuizSerializer(serializers.ModelSerializer):
    """Serializer for DailyQuiz."""
    
    slot_display = serializers.CharField(source='get_slot_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    
    class Meta:
        model = DailyQuiz
        fields = [
            'id', 'quiz_title', 'date', 'slot', 'slot_display',
            'keys_required', 'xp_multiplier', 'difficulty', 'difficulty_display'
        ]
        read_only_fields = fields


class RewardedVideoAdSerializer(serializers.ModelSerializer):
    """Serializer for RewardedVideoAd."""
    
    ad_network_display = serializers.CharField(source='get_ad_network_display', read_only=True)
    
    class Meta:
        model = RewardedVideoAd
        fields = [
            'id', 'title', 'ad_network', 'ad_network_display',
            'reward_keys', 'reward_xp', 'min_watch_duration_seconds',
            'completion_rate'
        ]
        read_only_fields = fields


class AdViewSerializer(serializers.ModelSerializer):
    """Serializer for AdView."""
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = AdView
        fields = [
            'id', 'status', 'status_display', 'watch_duration_seconds',
            'is_flagged_fraud', 'fraud_reason', 'created_at', 'completed_at'
        ]
        read_only_fields = fields


class DailyQuizUnlockSerializer(serializers.ModelSerializer):
    """Serializer for DailyQuizUnlock."""
    
    class Meta:
        model = DailyQuizUnlock
        fields = [
            'keys_earned', 'keys_required', 'is_unlocked',
            'is_completed', 'unlocked_at', 'expires_at'
        ]
        read_only_fields = fields


class KeyLedgerSerializer(serializers.ModelSerializer):
    """Serializer for KeyLedger."""
    
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    class Meta:
        model = KeyLedger
        fields = [
            'id', 'transaction_type', 'transaction_type_display',
            'amount', 'balance_after', 'description', 'created_at'
        ]
        read_only_fields = fields
