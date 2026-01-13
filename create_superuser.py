# Create superuser for testing
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizzy.settings')
django.setup()

from accounts.models import CustomUser, College

# Create college
college, _ = College.objects.get_or_create(
    code='ADMIN_COL',
    defaults={'name': 'Admin College', 'city': 'Admin City', 'state': 'Admin State'}
)

# Create superuser
if not CustomUser.objects.filter(email='admin@quizzy.com').exists():
    admin = CustomUser.objects.create_superuser(
        email='admin@quizzy.com',
        password='admin123',
        full_name='Admin User',
        college=college
    )
    print("[OK] Superuser created: admin@quizzy.com / admin123")
else:
    print("[OK] Superuser already exists")
