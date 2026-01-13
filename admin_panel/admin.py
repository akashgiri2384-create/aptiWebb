"""Django admin for admin_panel"""
from django.contrib import admin
from django.utils.html import format_html
from .models import AdminUser, FeatureToggle, AuditLog, QuizTemplate

@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'is_active', 'actions_count', 'appointed_at']
    list_filter = ['role', 'is_active']
    search_fields = ['user__email']
    readonly_fields = ['appointed_at', 'last_login', 'actions_count']

@admin.register(FeatureToggle)
class FeatureToggleAdmin(admin.ModelAdmin):
    list_display = ['feature_name', 'status_display', 'rollout_percentage', 'updated_at']
    list_filter = ['is_enabled']
    search_fields = ['feature_name']
    
    def status_display(self, obj):
        if obj.is_enabled:
            return format_html('<span style="color: green;">✓ ON</span>')
        return format_html('<span style="color: red;">✗ OFF</span>')
    status_display.short_description = 'Status'

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action_type', 'admin_user', 'description', 'success_display', 'created_at']
    list_filter = ['action_type', 'success', 'created_at']
    search_fields = ['admin_user__email', 'description']
    readonly_fields = ['admin_user', 'action_type', 'description', 'success', 'created_at']
    
    def success_display(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: red;">✗</span>')
    success_display.short_description = 'Status'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(QuizTemplate)
class QuizTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
