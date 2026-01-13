"""
Admin panel models - COMPLETE IMPLEMENTATION.

Models:
- AdminUser: Extended admin with roles and permissions
- FeatureToggle: Feature flags for gradual rollout
- AuditLog: Audit trail for admin actions
- QuizTemplate: CSV import templates
"""

from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class AdminUser(models.Model):
    """Extended admin user with roles and permissions."""
    
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('content_admin', 'Content Admin'),
        ('moderator', 'Moderator'),
        ('analyst', 'Analyst'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    
    # Role
    role = models.CharField('Role', max_length=20, choices=ROLE_CHOICES, db_index=True)
    
    # Permissions (JSON for flexibility)
    permissions = models.JSONField('Permissions', default=dict,
                                   help_text='{"quiz_create": true, "user_ban": true, ...}')
    
    # Status
    is_active = models.BooleanField('Active', default=True)
    
    # Metadata
    appointed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointed_admins'
    )
    appointed_at = models.DateTimeField('Appointed At', auto_now_add=True)
    
    # Activity
    last_login = models.DateTimeField('Last Login', null=True, blank=True)
    actions_count = models.IntegerField('Actions Count', default=0)
    
    class Meta:
        db_table = 'admin_adminuser'
        verbose_name = 'Admin User'
        verbose_name_plural = 'Admin Users'
        ordering = ['-appointed_at']
        indexes = [
            models.Index(fields=['role', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_role_display()}"
    
    def has_permission(self, perm):
        """Check if admin has specific permission."""
        return self.permissions.get(perm, False)


class FeatureToggle(models.Model):
    """Feature flags for gradual rollout."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Feature
    feature_name = models.CharField('Feature Name', max_length=100, unique=True, db_index=True)
    description = models.TextField('Description', blank=True)
    
    # Status
    is_enabled = models.BooleanField('Enabled', default=False)
    
    # Rollout
    rollout_percentage = models.IntegerField('Rollout %', default=0,
                                            help_text='0-100%, for gradual rollout')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'admin_featuretoggle'
        verbose_name = 'Feature Toggle'
        verbose_name_plural = 'Feature Toggles'
        ordering = ['-updated_at']
    
    def __str__(self):
        status = 'ON' if self.is_enabled else 'OFF'
        return f"{self.feature_name} ({status})"


class AuditLog(models.Model):
    """Audit trail for admin actions."""
    
    ACTION_TYPES = [
        ('user_created', 'User Created'),
        ('user_banned', 'User Banned'),
        ('user_approved', 'User Approved'),
        ('quiz_created', 'Quiz Created'),
        ('quiz_published', 'Quiz Published'),
        ('quiz_archived', 'Quiz Archived'),
        ('csv_import', 'CSV Import'),
        ('csv_export', 'CSV Export'),
        ('xp_granted', 'XP Granted'),
        ('xp_revoked', 'XP Revoked'),
        ('feature_toggle', 'Feature Toggle'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Actor
    admin_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_actions'
    )
    
    # Action
    action_type = models.CharField('Action Type', max_length=50, choices=ACTION_TYPES, db_index=True)
    description = models.TextField('Description')
    
    # Target (flexible)
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_targets'
    )
    target_quiz = models.ForeignKey(
        'quizzes.Quiz',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    
    # Details
    details = models.JSONField('Details', default=dict, help_text='Additional metadata')
    
    # Status
    success = models.BooleanField('Success', default=True)
    error_message = models.TextField('Error Message', blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'admin_auditlog'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin_user', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
        ]
    
    def __str__(self):
        actor = self.admin_user.email if self.admin_user else 'System'
        return f"{self.get_action_type_display()} by {actor}"


class QuizTemplate(models.Model):
    """Template for CSV import of quizzes."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Name
    name = models.CharField('Template Name', max_length=255)
    description = models.TextField('Description', blank=True)
    
    # Configuration (column mapping)
    config = models.JSONField('Configuration',
                             help_text='Column mapping: {"column_0": "question_text", ...}')
    
    # Status
    is_active = models.BooleanField('Active', default=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_quiztemplate'
        verbose_name = 'Quiz Template'
        verbose_name_plural = 'Quiz Templates'
    
    def __str__(self):
        return self.name
