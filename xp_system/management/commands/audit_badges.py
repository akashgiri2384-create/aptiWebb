from django.core.management.base import BaseCommand
from xp_system.models import Badge

class Command(BaseCommand):
    help = 'Audits Badge Names for Mapping Verification'

    def handle(self, *args, **kwargs):
        # Filter for Rank badges
        badges = Badge.objects.filter(rarity='rank').order_by('rank_order')
        
        self.stdout.write(f"Found {badges.count()} Rank Badges.")
        self.stdout.write("-" * 40)
        self.stdout.write(f"{'Rank':<5} | {'Name (Exact String)':<30} | {'XP Thr':<10}")
        self.stdout.write("-" * 40)
        
        for b in badges:
            self.stdout.write(f"{b.rank_order:<5} | '{b.name}'{' '*(28-len(b.name))} | {b.xp_threshold}")
            
        self.stdout.write("-" * 40)
        
        # Check specific "First of Tier" badges against expected keys
        expected_keys = [
            "Bronze I", "Silver I", "Emberlaure I", "Tome I", 
            "Eternal I", "Arcane I", "Mystic I", "Verdant I",
            "Frostheart I", "Crystal I", "Infernos I", "Stellar I",
            "Crown I", "Lunar I", "Galactic I", "Grandmaster I"
        ]
        
        self.stdout.write("\nMAPPING CHECK:")
        for key in expected_keys:
            exists = badges.filter(name=key).exists()
            status = "MATCH" if exists else "MISSING"
            self.stdout.write(f"Key '{key}': {status}")
