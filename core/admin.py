"""
Django admin configuration for core app.
"""

from django.contrib import admin
from .models import PlatformSettings, FeatureFlag


@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    """Admin interface for PlatformSettings."""
    
    list_display = ['key', 'value', 'updated_at']
    search_fields = ['key', 'description']
    ordering = ['key']


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    """Admin interface for FeatureFlag."""
    
    list_display = ['name', 'is_enabled', 'updated_at']
    list_filter = ['is_enabled']
    search_fields = ['name', 'description']
    ordering = ['name']
