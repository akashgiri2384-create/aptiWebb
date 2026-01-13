from django.contrib import admin
from .models import CollegeReportSubscription

@admin.register(CollegeReportSubscription)
class CollegeReportSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('get_college_name', 'recipient_email', 'frequency', 'is_active', 'last_sent_at')
    list_filter = ('frequency', 'is_active')
    search_fields = ('college__name', 'recipient_email')
    
    @admin.display(ordering='college__name', description='College Name')
    def get_college_name(self, obj):
        return obj.college.name

    @admin.action(description='Send Report Now')
    def send_report_now(self, request, queryset):
        success_count = 0
        from .services import send_college_report
        
        for sub in queryset:
            success, msg = send_college_report(sub)
            if success:
                success_count += 1
            else:
                self.message_user(request, f"Error for {sub.college.name}: {msg}", level='error')
        
        self.message_user(request, f"Successfully sent {success_count} reports.")

    actions = [send_report_now]
