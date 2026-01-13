"""
Core platform models.
"""

from django.db import models


class PlatformSettings(models.Model):
    """Global platform settings."""
    
    key = models.CharField(max_length=255, unique=True, primary_key=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'platform_settings'
        verbose_name = 'Platform Setting'
        verbose_name_plural = 'Platform Settings'
    
    def __str__(self):
        return f'{self.key}: {self.value}'


class FeatureFlag(models.Model):
    """Feature flags for A/B testing and gradual rollouts."""
    
    name = models.CharField(max_length=255, unique=True, primary_key=True)
    is_enabled = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'feature_flags'
        verbose_name = 'Feature Flag'
        verbose_name_plural = 'Feature Flags'
    
    def __str__(self):
        return f'{self.name}: {"Enabled" if self.is_enabled else "Disabled"}'
