import os
import django
from django.utils.text import slugify

import sys
# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizzy.settings')
django.setup()

# Force UTF-8 for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from quizzes.models import Category

CATEGORIES = [
    # General
    ('Verbal Ability', '🗣️'),
    ('Logical Reasoning', '🧠'),
    ('Aptitude', '📊'),
    ('Data Interpretation', '📈'),
    
    # Computer Science Core
    ('Computer Basics', '💻'),
    ('Operating System', '⚙️'),
    ('DBMS', '🗄️'),
    ('Networking', '🌐'),
    ('Data Structures', '🌲'),
    ('Algorithms', '⚡'),
    
    # Advanced Tech
    ('Cyber Security', '🔐'),
    ('AI & ML Basics', '🤖'),
    ('Cloud Computing', '☁️'),
    ('DevOps', '♾️'),
    ('Ethical Hacking', '🕵️‍♂️'),
    
    # Programming
    ('Python', '🐍'),
    ('Java', '☕'),
    ('C++', '💻'),
    ('SQL', '🗄️'),
    ('JavaScript', '📜'),
    
    # General
    ('History', '📜'),
    ('Science', '🔬'),
    ('Geography', '🌍'),
    ('GK', '💡'),
    ('English', '📖'),
    ('Math', '🧮'),
]

def seed_categories():
    print("🌱 Seeding Categories...")
    
    for name, emoji in CATEGORIES:
        slug = slugify(name)
        category, created = Category.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'emoji': emoji,
                'is_active': True,
                'color': '#4F46E5',  # Default Indigo
                'order': 10
            }
        )
        
        if created:
            print(f"✅ Created: {name}")
        else:
            print(f"ℹ️ Exists: {name}")

    print("\n✨ Done! Admin panel updated.")

if __name__ == '__main__':
    seed_categories()
