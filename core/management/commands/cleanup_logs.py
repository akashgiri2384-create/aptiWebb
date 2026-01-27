from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from dashboard.models import UserActivityLog
from daily_quizzes.models import AdView
from django.core.management import call_command
import logging

logger = logging.getLogger('django')

class Command(BaseCommand):
    help = 'Cleans up old logs to free up database space on free tiers.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting cleanup...")
        
        # 1. Calculate cutoff time (48 hours ago)
        cutoff = timezone.now() - timedelta(hours=48)
        
        # 2. Delete UserActivityLogs
        count, _ = UserActivityLog.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(f"Deleted {count} old UserActivityLog entries.")
        logger.info(f"Cleanup: Deleted {count} UserActivityLog entries older than {cutoff}")
        
        # 3. Delete AdViews
        count_ads, _ = AdView.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(f"Deleted {count_ads} old AdView entries.")
        logger.info(f"Cleanup: Deleted {count_ads} AdView entries older than {cutoff}")
        
        # 4. Clear expired sessions
        call_command('clearsessions')
        self.stdout.write("Cleared expired sessions.")
        
        self.stdout.write(self.style.SUCCESS('Cleanup completed successfully.'))
