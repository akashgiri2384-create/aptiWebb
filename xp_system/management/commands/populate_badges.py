from django.core.management.base import BaseCommand
from xp_system.models import Badge

class Command(BaseCommand):
    help = 'Populates the database with initial achievement badges'

    def handle(self, *args, **kwargs):
        badges = [
            {
                'name': 'Quiz Novice',
                'description': 'Attempt your first 5 quizzes',
                'icon': 'fa-book-open',
                'emoji': '📘',
                'rarity': 'common',
                'unlock_type': 'quizzes_attempted',
                'unlock_requirement': {'count': 5},
                'xp_reward': 50
            },
            {
                'name': 'Quiz Master',
                'description': 'Attempt 50 quizzes',
                'icon': 'fa-graduation-cap',
                'emoji': '🎓',
                'rarity': 'epic',
                'unlock_type': 'quizzes_attempted',
                'unlock_requirement': {'count': 50},
                'xp_reward': 500
            },
            {
                'name': 'Sharpshooter',
                'description': 'Score 100% on any quiz',
                'icon': 'fa-crosshairs',
                'emoji': '🎯',
                'rarity': 'rare',
                'unlock_type': 'accuracy_single',
                'unlock_requirement': {'percentage': 100},
                'xp_reward': 100
            },
            {
                'name': 'Streak Starter',
                'description': 'Maintain a 3-day streak',
                'icon': 'fa-fire',
                'emoji': '🔥',
                'rarity': 'common',
                'unlock_type': 'streak_days',
                'unlock_requirement': {'days': 3},
                'xp_reward': 50
            },
            {
                'name': 'Week Warrior',
                'description': 'Maintain a 7-day streak',
                'icon': 'fa-calendar-check',
                'emoji': '🗓️',
                'rarity': 'uncommon',
                'unlock_type': 'streak_days',
                'unlock_requirement': {'days': 7},
                'xp_reward': 150
            },
            {
                'name': 'XP Hunter',
                'description': 'Earn 1,000 Total XP',
                'icon': 'fa-star',
                'emoji': '⭐',
                'rarity': 'uncommon',
                'unlock_type': 'total_xp',
                'unlock_requirement': {'amount': 1000},
                'xp_reward': 100,
                'image_path': None
            }
        ]

        created_count = 0
        for badge_data in badges:
            # Ensure image_path is None if not set
            if 'image_path' not in badge_data:
                badge_data['image_path'] = None
                
            badge, created = Badge.objects.update_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created badge: {badge.name}'))
            else:
                 self.stdout.write(f'Updated badge: {badge.name}')

        self.stdout.write(self.style.SUCCESS(f'Successfully populated {created_count} achievement badges'))

        # --- Populate Rank Badges (1-80) ---
        self.stdout.write("Populating 80 Rank Badges...")
        
        tiers = [
            # (Name, Steps, FilePattern, Extension) - 5 steps each implies 16 tiers = 80 badges
            ('Bronze', 'bronze', 'png'),
            ('Silver', 'silver', 'png'),
            ('Emberlaure', 'Emberlaure', 'png'),
            ('Tome', 'Tome', 'png'),
            ('Eternal', 'Eternal', 'png'),
            ('Arcane', 'Arcane', 'png'),
            ('Mystic', 'Mystic', 'png'),
            ('Verdant', 'Verdant', 'png'),
            ('Frostheart', 'Frostheart', 'png'),
            ('Crystal', 'Crystal', 'png'),
            ('Infernos', 'Infernos', 'png'),
            ('Stellar', 'Stellar', 'png'),
            ('Crown', 'Crown', 'png'),
            ('Lunar', 'Lunar', 'png'),
            ('Galactic', 'Galactic', 'png'),
            ('Grandmaster', 'grandmaster', 'jpeg'), # Note .jpeg for grandmaster
        ]

        rank_count = 0
        global_rank_index = 1
        
        for tier_name, file_key, ext in tiers:
            for step in range(1, 6): # 1 to 5
                # correct file name anomalies handle
                # e.g. "1_bronze-1.png", "10-silver-5.png", "11_Emberlaure-1.png"
                current_rank = global_rank_index
                
                # Construct expected filename
                # Standard format: {Index}_{Name}-{Step}.{ext}
                # Handling known anomalies based on list:
                # 10-silver-5.png (hyphen instead of underscore)
                # 41_ Frostheart-1.png (space)
                # 64-Crown-4.png (hyphen)
                # 55_Infernos-5.png (double check directory list)
                
                filename = f"{current_rank}_{file_key}-{step}.{ext}"
                
                # Manual overrides for dirty filenames
                if current_rank == 10: filename = "10-silver-5.png"
                if current_rank == 41: filename = "41_ Frostheart-1.png"
                if current_rank == 64: filename = "64-Crown-4.png"
                
                # XP Threshold: simple quadratic curve
                # Rank 1 = 100, Rank 80 = ~6M
                xp_threshold = (current_rank ** 2) * 100
                
                badge_name = f"{tier_name} {self.int_to_roman(step)}"
                
                badge, created = Badge.objects.update_or_create(
                    name=badge_name,
                    defaults={
                        'description': f'Reach Rank {current_rank}: {tier_name} Tier',
                        'icon': 'fa-medal', # Fallback
                        'emoji': '🎖️',
                        'rarity': 'rank',
                        'image_path': f'images/badges/{filename}',
                        'rank_order': current_rank,
                        'xp_threshold': xp_threshold,
                        'xp_reward': 0, # Ranks don't give XP, they ARE the reward
                        'unlock_type': 'total_xp', # Descriptive
                        'unlock_requirement': {'amount': xp_threshold}
                    }
                )
                if created:
                    self.stdout.write(f"Created Rank: {badge_name}")
                rank_count += 1
                global_rank_index += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully populated {rank_count} rank badges'))

    def int_to_roman(self, num):
        val = [
            (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
            (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
            (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
        ]
        syb = []
        while num > 0:
            for i, r in val:
                while num >= i:
                    syb.append(r)
                    num -= i
        return "".join(syb)
