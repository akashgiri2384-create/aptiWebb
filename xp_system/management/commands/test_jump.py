from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from xp_system.models import UserStats, Badge, UserBadge
from xp_system.services import BadgeService, XPService

User = get_user_model()

class Command(BaseCommand):
    help = 'Simulates a Rank Jump to test Animation Logic'

    def handle(self, *args, **kwargs):
        # 1. Setup User
        email = "test_jump_user@example.com"
        User.objects.filter(email=email).delete() 
        user = User.objects.create_user(email=email, password="password123")
        stats = UserStats.objects.create(user=user)
        
        self.stdout.write(f"Created User: {user.email}")

        # 2. Give Bronze V (Badge + XP)
        # Bronze I=100 ... Bronze V (~2500 XP)
        bronze_v_xp = 2500 
        stats.total_xp = bronze_v_xp
        stats.season_xp = bronze_v_xp
        stats.save()
        
        # Manually award badges up to Bronze V to simulate "Previous State"
        # Ranks 1 to 5
        badges_1_to_5 = Badge.objects.filter(rarity='rank', rank_order__lte=5)
        for b in badges_1_to_5:
            UserBadge.objects.create(user=user, badge=b)
            
        self.stdout.write(f"Setup complete. User at Bronze V (Rank 5). Badges: {badges_1_to_5.count()}")

        # 3. Perform JUMP to Emberlaure I (Rank 11)
        # Rank 11 Threshold: 11^2 * 100 = 12100 XP.
        jump_xp = 12200 # Slightly above
        
        self.stdout.write(f"--- EXECUTING JUMP TO {jump_xp} XP (Target: Emberlaure I) ---")
        
        stats.season_xp = jump_xp
        stats.save()
        
        # 4. Call check_rank_up (The Logic Under Test)
        # We intercept the logging or return value by mocking? 
        # Or just rely on the logging output in terminal.
        # But to be sure, let's call it and inspect the logs/db if we could.
        # Since we can't easily inspect logs programmatically here without setup, 
        # We will wrap the Service method or just trust the Console Output we see when running.
        
        BadgeService.check_rank_up(user, stats)
        
        # 5. Check Result
        # We can check the UserActivityLog to see what was "Triggered"
        from dashboard.models import UserActivityLog
        log = UserActivityLog.objects.filter(user=user, activity_type='rank_change').order_by('-created_at').first()
        
        if log:
            self.stdout.write(self.style.SUCCESS(f"Activity Logged: {log.description}"))
            meta = log.metadata
            self.stdout.write(f"Metadata: {meta}")
            
            if meta.get('major_rank_up'):
                self.stdout.write(self.style.SUCCESS(f"ANIMATION TRIGGERED: YES"))
                self.stdout.write(f"Video: {meta.get('video_path')}")
                if "silver" in meta.get('video_path', '').lower() or "emberlaure" in meta.get('video_path', '').lower():
                    self.stdout.write(self.style.SUCCESS(f"CORRECT VIDEO: {meta.get('video_path')} Selected."))
                else:
                    self.stdout.write(self.style.ERROR(f"WRONG VIDEO: {meta.get('video_path')}"))
            else:
                self.stdout.write(self.style.ERROR("ANIMATION NOT TRIGGERED (major_rank_up=False)"))
                
        else:
            self.stdout.write(self.style.ERROR("No Activity Log found! Logic Crash?"))
