from django.core.management.base import BaseCommand
from xp_system.models import Badge
import math
import os
import re
from django.conf import settings

class Command(BaseCommand):
    help = 'Seed 80 Rank Badges with dynamic image mapping'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding Ranks...')

        # Config
        MIN_XP = 100
        MAX_XP = 1000000
        TOTAL_RANKS = 80
        
        # Calculate multiplier for geometric progression
        multiplier = (MAX_XP / MIN_XP) ** (1 / (TOTAL_RANKS - 1))

        # Rank Names Configuration
        rank_names = [
            (1, 5, 'Bronze'),
            (6, 10, 'Silver'),
            (11, 15, 'Emberlaure'),
            (16, 20, 'Tome'),
            (21, 25, 'Eternal'),
            (26, 30, 'Arcane'),
            (31, 35, 'Mystic'),
            (36, 40, 'Verdant'),
            (41, 45, 'Frostheart'),
            (46, 50, 'Crystal'),
            (51, 55, 'Infernos'),
            (56, 60, 'Stellar'),
            (61, 65, 'Crown'),
            (66, 70, 'Lunar'),
            (71, 75, 'Galactic'),
            (76, 80, 'Grandmaster'),
        ]

        # 1. Build File Map from Directory
        badges_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'badges')
        file_map = {} # { rank_num: filename }
        
        if not os.path.exists(badges_dir):
            self.stdout.write(self.style.ERROR(f'Badges directory not found: {badges_dir}'))
            return

        # Regex to capture finding starting number: e.g. "1_bronze.png" -> 1, "10-silver.png" -> 10
        # Tolerates space like "41_ Frostheart"
        file_pattern = re.compile(r'^(\d+)[-_\s].+')

        files = os.listdir(badges_dir)
        for f in files:
            match = file_pattern.match(f)
            if match:
                rank_num = int(match.group(1))
                file_map[rank_num] = f
        
        self.stdout.write(f"Found {len(file_map)} mapped badge images.")

        # 2. Clear existing Rank badges
        Badge.objects.filter(rarity='rank').delete()
        
        created_count = 0

        for rank_num in range(1, TOTAL_RANKS + 1):
            # Calculate Threshold
            threshold = int(MIN_XP * (multiplier ** (rank_num - 1)))
            if threshold > 1000:
                threshold = round(threshold / 10) * 10
            
            # Determine Name
            name_display = "Unknown"
            sub_level = 1
            for start, end, display in rank_names:
                if start <= rank_num <= end:
                    name_display = display
                    sub_level = rank_num - start + 1
                    break
            
            # Find Filename
            filename = file_map.get(rank_num)
            
            if not filename:
                self.stdout.write(self.style.WARNING(f"Missing image for Rank {rank_num}. Using default."))
                # Fallback to a generic name if missing? Or just keep empty?
                # Let's try to guess a standard one just in case file listing failed or loop logic
                filename = f"{rank_num}_badge.png" 

            Badge.objects.create(
                name=f"{name_display} {sub_level}",
                description=f"Reach Rank {rank_num}: {name_display} Level {sub_level}",
                rank_order=rank_num,
                xp_threshold=threshold,
                image_path=f"images/badges/{filename}",
                rarity='rank',
                icon='fa-medal', 
                emoji='🏅'
            )
            created_count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {created_count} rank badges.'))
