from django.db import models

class CollegeReportSubscription(models.Model):
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    college = models.ForeignKey(
        'accounts.College',
        on_delete=models.CASCADE,
        related_name='report_subscriptions',
        help_text="Select the college for this report.",
        null=True,
        blank=True
    )
    recipient_email = models.EmailField(
        help_text="Target email address for the report (e.g., placement@college.edu)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to pause sending reports"
    )
    frequency = models.CharField(
        max_length=10, 
        choices=FREQUENCY_CHOICES, 
        default='weekly'
    )
    last_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['college__name']
        verbose_name = "College Report Subscription"
        verbose_name_plural = "College Report Subscriptions"

    def __str__(self):
        return f"{self.college.name} -> {self.recipient_email} ({self.frequency})"
