
from django.core.management.base import BaseCommand
from accounts.models import College
from accounts.constants import COLLEGE_NAMES
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Seeds the database with the official list of Colleges.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting College Seed...")
        created_count = 0
        
        # Disable all others? Optional. For now, just ensuring these exist.
        
        for name in COLLEGE_NAMES:
            # Generate a code based on slug
            code = slugify(name)[:50].upper()
            
            college, created = College.objects.get_or_create(
                name=name,
                defaults={
                    'code': code,
                    'city': 'Pune' if 'Pune' in name else 'Maharashtra',
                    'state': 'Maharashtra',
                    'country': 'India',
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {name}"))
            else:
                self.stdout.write(f"Exists: {name}")

        self.stdout.write(self.style.SUCCESS(f"Seeding Complete. Created {created_count} new colleges."))
