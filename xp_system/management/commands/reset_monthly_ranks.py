from django.core.management.base import BaseCommand
from django.db import transaction
from xp_system.models import UserStats, UserBadge, Badge
import logging

logger = logging.getLogger('quizzy')

class Command(BaseCommand):
    help = 'Reset monthly Season XP and Rank Badges'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting Monthly Rank Reset...')
        
        try:
            with transaction.atomic():
                # 1. Reset Season XP for all users
                stats_updated = UserStats.objects.update(season_xp=0)
                self.stdout.write(f'Reset Season XP for {stats_updated} users.')
                
                # 2. Delete all Rank Badges earned by users
                # We need to identify badges with rarity='rank'
                rank_badges = Badge.objects.filter(rarity='rank')
                deleted_count, _ = UserBadge.objects.filter(badge__in=rank_badges).delete()
                self.stdout.write(f'Removed {deleted_count} rank badges from users.')
                
                # 3. Log
                logger.info(f"Monthly Reset Completed: {stats_updated} stats reset, {deleted_count} badges removed.")
                self.stdout.write(self.style.SUCCESS('Monthly Reset Completed Successfully.'))
                
        except Exception as e:
            logger.error(f"Monthly Reset Failed: {e}")
            self.stdout.write(self.style.ERROR(f'Monthly Reset Failed: {e}'))
