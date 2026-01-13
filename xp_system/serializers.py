"""DRF serializers for xp_system - PLACEHOLDER"""
from rest_framework import serializers
from .models import XPLog, Badge, UserBadge

class XPLogSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    class Meta:
        model = XPLog
        fields = ['created_at', 'transaction_type', 'type_display', 'amount', 'balance_after', 'description', 'metadata']

class BadgeSerializer(serializers.ModelSerializer):
    rarity_display = serializers.CharField(source='get_rarity_display', read_only=True)
    class Meta:
        model = Badge
        fields = ['name', 'description', 'emoji', 'rarity', 'rarity_display', 'xp_reward']

class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer()
    class Meta:
        model = UserBadge
        fields = ['badge', 'unlocked_at']
