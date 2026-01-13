
import os
import django
import sys

# Setup Django
sys.path.append(r"d:\aptiWeb")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aptitude_quiz.settings')
django.setup()

from xp_system.models import Badge

# -------------------------------------------------------------------
# DUPLICATE LOGIC FROM SERVICES.PY FOR TESTING
# -------------------------------------------------------------------
def get_tier_name(rank_name):
    rank_lower = rank_name.lower()
    
    if 'grandmaster-5' in rank_lower or 'grandmaster 5' in rank_lower:
        return 'Grandmaster-5'
    
    tiers = [
        'Bronze', 'Silver', 'Emberlaure', 'Tome', 'Eternal', 
        'Arcane', 'Mystic', 'Verdant', 'Frostheart', 'Crystal', 
        "Inferno's", 'Infernos', 'Stellar', 'Crown', 'Lunar', 
        'Galactic', 'Grandmaster'
    ]
    
    for tier in tiers:
        if tier.lower() in rank_lower:
            return "Infernos" if "inferno" in tier.lower() else tier
            
    return 'Bronze' # Default fallback

video_map = {
    'Bronze': '1_bronze-1.mp4',
    'Silver': '6_silver-1.mp4',
    'Emberlaure': '11_Emberlaure-11.mp4',
    'Tome': '16_Tome-1.mp4',
    'Eternal': '21_eternal-1.mp4',
    'Arcane': '26_Arcane-1.mp4',
    'Mystic': '31_Mystic-1.mp4',
    'Verdant': '36_Verdant-1.mp4',
    'Frostheart': '41_Frostheart-1.mp4',
    'Crystal': '46_Crystal-1.mp4', 
    'Infernos': '51_Infernos-1.mp4',
    'Stellar': '56_Stellar-1.mp4',
    'Crown': '61_Crown-1.mp4',
    'Lunar': '66_Lunar-1.mp4',
    'Galactic': '71_Galactic-1.mp4',
    'Grandmaster': '76_Grandmaster-1.mp4',
    'Grandmaster-5': '80_Grandmaster_5 -.mp4'
}

# -------------------------------------------------------------------
# AUDIT
# -------------------------------------------------------------------
print("\n--- Starting Badge Name Audit ---\n")

badges = Badge.objects.filter(rarity='rank').order_by('rank_order')

if not badges.exists():
    print("NO RANK BADGES FOUND IN DB!")
else:
    for badge in badges:
        detected_tier = get_tier_name(badge.name)
        has_video = detected_tier in video_map
        video_file = video_map.get(detected_tier, 'MISSING')
        
        status = "OK" if (has_video and detected_tier != 'Bronze') or (detected_tier == 'Bronze' and 'bronze' in badge.name.lower()) else "FAIL?"
        
        # If it defaulted to Bronze but name doesn't have bronze, it's a FAIL
        if detected_tier == 'Bronze' and 'bronze' not in badge.name.lower():
            status = "CRITICAL FAIL (Defaulted to Bronze)"
            
        print(f"Badge: '{badge.name}' -> Tier: '{detected_tier}' -> Video: {video_file} [{status}]")

print("\n--- Audit Complete ---")
