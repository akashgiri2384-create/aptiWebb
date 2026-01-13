"""DRF serializers for admin_panel - PLACEHOLDER"""
from rest_framework import serializers
from .models import AdminUser, FeatureToggle, AuditLog

class AdminUserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    class Meta:
        model = AdminUser
        fields = ['user', 'role', 'role_display', 'is_active', 'actions_count']

class FeatureToggleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureToggle
        fields = ['feature_name', 'description', 'is_enabled', 'rollout_percentage']

class AuditLogSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source='get_action_type_display', read_only=True)
    class Meta:
        model = AuditLog
        fields = ['action_type', 'action_display', 'description', 'success', 'created_at']
