import csv
import io
from datetime import timedelta
from django.core.management.base import BaseCommand
from reports.models import CollegeReportSubscription
from reports.services import send_college_report

class Command(BaseCommand):
    help = 'Sends automated weekly/monthly reports to college admins.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting College Report Automation...")
        
        subscriptions = CollegeReportSubscription.objects.filter(is_active=True)
        count = 0

        for sub in subscriptions:
            self.stdout.write(f"Processing subscription: {sub.college.name}")
            
            success, message = send_college_report(sub)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f"  - {message}"))
                count += 1
            else:
                self.stdout.write(self.style.WARNING(f"  - Failed/Skipped: {message}"))

        self.stdout.write(self.style.SUCCESS(f"Done. Sent {count} reports."))
