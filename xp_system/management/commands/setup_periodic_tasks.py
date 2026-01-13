from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

class Command(BaseCommand):
    help = 'Setup system periodic tasks'

    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up periodic tasks...')

        # 1. Create Schedule: 1st day of every month at 00:00 (Midnight)
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='0',
            day_of_month='1',
            month_of_year='*',
            day_of_week='*',
            timezone='UTC' # Or your specific timezone
        )
        
        if created:
             self.stdout.write(f'Created monthly crontab schedule: {schedule}')

        # 2. Create/Update Periodic Task
        task, created = PeriodicTask.objects.update_or_create(
            name='Reset Monthly Ranks',
            defaults={
                'crontab': schedule,
                'task': 'xp_system.tasks.reset_monthly_ranks', # Need to wrapper as Celery task
                'enabled': True,
                'description': 'Resets Season XP and Rank Badges on the 1st of every month.'
            }
        )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully configured periodic task: {task.name}'))
