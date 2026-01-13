
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizzy.settings')
django.setup()

from xp_system.models import Badge

def seed_badges():
    badges = [
        {
            'name': 'First Steps',
            'description': 'Complete your first quiz',
            'icon': 'flag',
            'emoji': '🏁',
            'rarity': 'common',
            'unlock_type': 'quizzes_attempted',
            'unlock_requirement': {'count': 1},
            'xp_reward': 50
        },
        {
            'name': 'Sharpshooter',
            'description': 'Get 100% accuracy in a quiz',
            'icon': 'target',
            'emoji': '🎯',
            'rarity': 'uncommon',
            'unlock_type': 'accuracy_single',
            'unlock_requirement': {'percentage': 100},
            'xp_reward': 100
        },
        {
            'name': 'Quiz Master',
            'description': 'Pass 10 quizzes',
            'icon': 'trophy',
            'emoji': '🏆',
            'rarity': 'rare',
            'unlock_type': 'quizzes_passed',
            'unlock_requirement': {'count': 10},
            'xp_reward': 500
        },
        {
            'name': 'Streak Starter',
            'description': 'Maintain a 3-day practice streak',
            'icon': 'fire',
            'emoji': '🔥',
            'rarity': 'common',
            'unlock_type': 'streak_days',
            'unlock_requirement': {'days': 3},
            'xp_reward': 150
        },
        {
            'name': 'Night Owl',
            'description': 'Complete a quiz after 10 PM',
            'icon': 'moon',
            'emoji': '🦉',
            'rarity': 'common',
            'unlock_type': 'time_range',
            'unlock_requirement': {'start': '22:00', 'end': '04:00'},
            'xp_reward': 75
        }
    ]

    print("Seeding badges...")
    for badge_data in badges:
        badge, created = Badge.objects.get_or_create(
            name=badge_data['name'],
            defaults=badge_data
        )
        if created:
            print(f"Created badge: {badge.name}")
        else:
            print(f"Badge already exists: {badge.name}")

if __name__ == '__main__':
    seed_badges()
