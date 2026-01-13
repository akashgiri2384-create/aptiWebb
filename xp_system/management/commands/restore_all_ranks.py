from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from xp_system.services import BadgeService
from xp_system.models import UserStats

class Command(BaseCommand):
    help = 'Restores rank badges for ALL users based on their current Season XP'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        users = User.objects.all()
        count = users.count()
        
        self.stdout.write(f'Checking ranks for {count} users...')
        
        restored_count = 0
        
        for user in users:
            try:
                # Ensure stats exist
                if not hasattr(user, 'xp_stats'):
                    UserStats.objects.create(user=user)
                    
                # The service will check existing vs eligible and award missing ones
                BadgeService.check_rank_up(user, user.xp_stats)
                restored_count += 1
                
                if restored_count % 100 == 0:
                    self.stdout.write(f'Processed {restored_count}/{count} users...')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error for user {user.email}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully processed {restored_count} users.'))
