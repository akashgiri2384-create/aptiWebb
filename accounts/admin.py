"""
Django admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import CustomUser, UserProfile, College, LoginSession, PasswordReset, OTPVerification


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Admin interface for CustomUser with comprehensive display."""
    
    list_display = [
        'email', 'full_name', 'college_display', 'user_type',
        'is_active', 'is_email_verified', 'login_count', 'created_at'
    ]
    list_filter = [
        'user_type', 'is_active', 'is_email_verified', 'is_mobile_verified',
        'is_banned', 'is_staff', 'is_superuser', 'created_at'
    ]
    search_fields = ['email', 'full_name', 'mobile_number', 'roll_number']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login_at', 'login_count']
    
    fieldsets = (
        ('Account', {
            'fields': ('id', 'email', 'password')
        }),
        ('Personal Information', {
            'fields': ('full_name', 'mobile_number')
        }),
        ('College Information', {
            'fields': ('college', 'year', 'branch', 'roll_number')
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_email_verified', 'is_mobile_verified', 
                      'is_banned', 'ban_reason')
        }),
        ('Terms & Privacy', {
            'fields': ('accepted_terms', 'accepted_terms_at', 
                      'accepted_privacy', 'accepted_privacy_at')
        }),
        ('User Type & Permissions', {
            'fields': ('user_type', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Metadata', {
            'fields': ('login_count', 'created_at', 'updated_at', 'last_login_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'college'),
        }),
    )
    
    def college_display(self, obj):
        """Display college name."""
        return obj.college.name if obj.college else '-'
    college_display.short_description = 'College'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of superusers."""
        if obj and obj.is_superuser:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    """Admin interface for College."""
    
    list_display = ['name', 'code', 'city', 'state', 'country', 'is_active', 'student_count', 'created_at']
    list_filter = ['is_active', 'state', 'country', 'created_at']
    search_fields = ['name', 'code', 'city', 'state']
    ordering = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'student_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'code')
        }),
        ('Location', {
            'fields': ('city', 'state', 'country')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('student_count', 'created_at', 'updated_at')
        }),
    )
    
    def student_count(self, obj):
        """Display number of students."""
        return obj.students.count()
    student_count.short_description = 'Students'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile."""
    
    list_display = [
        'user_display', 'total_quizzes_attempted', 'total_xp',
        'current_rank', 'accuracy_percentage', 'practice_streak', 'theme'
    ]
    list_filter = ['theme', 'email_notifications', 'push_notifications']
    search_fields = ['user__email', 'user__full_name']
    readonly_fields = [
        'id', 'total_quizzes_attempted', 'total_xp', 'current_rank',
        'accuracy_percentage', 'practice_streak', 'total_keys', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['user']
    
    fieldsets = (
        ('User', {
            'fields': ('id', 'user')
        }),
        ('Profile', {
            'fields': ('avatar', 'bio', 'theme')
        }),
        ('Notifications', {
            'fields': ('email_notifications', 'push_notifications')
        }),
        ('Statistics', {
            'fields': ('total_quizzes_attempted', 'total_xp', 'current_rank',
                      'accuracy_percentage', 'practice_streak', 'total_keys')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def user_display(self, obj):
        """Display user email."""
        return obj.user.email
    user_display.short_description = 'User'


@admin.register(LoginSession)
class LoginSessionAdmin(admin.ModelAdmin):
    """Admin interface for LoginSession."""
    
    list_display = [
        'user_display', 'ip_address', 'device_type', 'login_at',
        'is_active', 'is_suspicious_display', 'duration'
    ]
    list_filter = ['is_active', 'is_suspicious', 'device_type', 'login_at']
    search_fields = ['user__email', 'ip_address', 'user_agent']
    ordering = ['-login_at']
    readonly_fields = [
        'id', 'user', 'ip_address', 'user_agent', 'device_type',
        'login_at', 'logout_at', 'last_activity', 'duration'
    ]
    
    fieldsets = (
        ('Session', {
            'fields': ('id', 'user')
        }),
        ('Device Information', {
            'fields': ('ip_address', 'user_agent', 'device_type')
        }),
        ('Lifecycle', {
            'fields': ('login_at', 'logout_at', 'last_activity', 'duration')
        }),
        ('Status', {
            'fields': ('is_active', 'is_suspicious')
        }),
    )
    
    def user_display(self, obj):
        """Display user email."""
        return obj.user.email
    user_display.short_description = 'User'
    
    def is_suspicious_display(self, obj):
        """Display suspicious status with color."""
        if obj.is_suspicious:
            return format_html('<span style="color: red;">⚠ Suspicious</span>')
        return format_html('<span style="color: green;">✓ Normal</span>')
    is_suspicious_display.short_description = 'Status'
    
    def duration(self, obj):
        """Calculate session duration."""
        if obj.logout_at:
            delta = obj.logout_at - obj.login_at
            minutes = int(delta.total_seconds() / 60)
            return f"{minutes} minutes"
        return "Active"
    duration.short_description = 'Duration'


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    """Admin interface for PasswordReset."""
    
    list_display = [
        'user_display', 'token_preview', 'created_at',
        'expires_at', 'is_used', 'is_expired_display'
    ]
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'token']
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'user', 'token', 'created_at', 'expires_at',
        'is_used', 'used_at', 'is_expired_display'
    ]
    
    fieldsets = (
        ('Reset Request', {
            'fields': ('id', 'user', 'token')
        }),
        ('Validity', {
            'fields': ('created_at', 'expires_at', 'is_expired_display')
        }),
        ('Usage', {
            'fields': ('is_used', 'used_at')
        }),
    )
    
    def user_display(self, obj):
        """Display user email."""
        return obj.user.email
    user_display.short_description = 'User'
    
    def token_preview(self, obj):
        """Display token preview."""
        return f"{obj.token[:20]}..."
    token_preview.short_description = 'Token'
    
    def is_expired_display(self, obj):
        """Display expiration status."""
        if obj.is_expired():
            return format_html('<span style="color: red;">✗ Expired</span>')
        return format_html('<span style="color: green;">✓ Valid</span>')
    is_expired_display.short_description = 'Validity'
