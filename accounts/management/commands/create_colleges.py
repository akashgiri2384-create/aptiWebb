"""
Management command to populate initial college data.

Usage:
    python manage.py create_colleges
"""

from django.core.management.base import BaseCommand
from accounts.models import College


class Command(BaseCommand):
    help = 'Create initial college data for Quizzy platform'
    
    def handle(self, *args, **options):
        """Create sample colleges."""
        
        colleges_data = [
            # IITs
            {'name': 'Indian Institute of Technology Delhi', 'code': 'IITD', 'city': 'New Delhi', 'state': 'Delhi'},
            {'name': 'Indian Institute of Technology Bombay', 'code': 'IITB', 'city': 'Mumbai', 'state': 'Maharashtra'},
            {'name': 'Indian Institute of Technology Kanpur', 'code': 'IITK', 'city': 'Kanpur', 'state': 'Uttar Pradesh'},
            {'name': 'Indian Institute of Technology Madras', 'code': 'IITM', 'city': 'Chennai', 'state': 'Tamil Nadu'},
            {'name': 'Indian Institute of Technology Kharagpur', 'code': 'IITKGP', 'city': 'Kharagpur', 'state': 'West Bengal'},
            {'name': 'Indian Institute of Technology Roorkee', 'code': 'IITR', 'city': 'Roorkee', 'state': 'Uttarakhand'},
            {'name': 'Indian Institute of Technology Guwahati', 'code': 'IITG', 'city': 'Guwahati', 'state': 'Assam'},
            {'name': 'Indian Institute of Technology Hyderabad', 'code': 'IITH', 'city': 'Hyderabad', 'state': 'Telangana'},
            
            # NITs
            {'name': 'National Institute of Technology Trichy', 'code': 'NITT', 'city': 'Tiruchirappalli', 'state': 'Tamil Nadu'},
            {'name': 'National Institute of Technology Karnataka', 'code': 'NITK', 'city': 'Surathkal', 'state': 'Karnataka'},
            {'name': 'National Institute of Technology Warangal', 'code': 'NITW', 'city': 'Warangal', 'state': 'Telangana'},
            {'name': 'National Institute of Technology Calicut', 'code': 'NITC', 'city': 'Calicut', 'state': 'Kerala'},
            {'name': 'National Institute of Technology Rourkela', 'code': 'NITR', 'city': 'Rourkela', 'state': 'Odisha'},
            
            # IIITs
            {'name': 'International Institute of Information Technology Hyderabad', 'code': 'IIITH', 'city': 'Hyderabad', 'state': 'Telangana'},
            {'name': 'International Institute of Information Technology Bangalore', 'code': 'IIITB', 'city': 'Bangalore', 'state': 'Karnataka'},
            
            # Other premier institutes
            {'name': 'Delhi Technological University', 'code': 'DTU', 'city': 'New Delhi', 'state': 'Delhi'},
            {'name': 'Netaji Subhas University of Technology', 'code': 'NSUT', 'city': 'New Delhi', 'state': 'Delhi'},
            {'name': 'Birla Institute of Technology and Science Pilani', 'code': 'BITS', 'city': 'Pilani', 'state': 'Rajasthan'},
            {'name': 'Vellore Institute of Technology', 'code': 'VIT', 'city': 'Vellore', 'state': 'Tamil Nadu'},
            {'name': 'SRM Institute of Science and Technology', 'code': 'SRM', 'city': 'Chennai', 'state': 'Tamil Nadu'},
        ]
        
        created_count = 0
        skipped_count = 0
        
        for college_data in colleges_data:
            college, created = College.objects.get_or_create(
                code=college_data['code'],
                defaults={
                    'name': college_data['name'],
                    'city': college_data['city'],
                    'state': college_data['state'],
                    'country': 'India',
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {college.name} ({college.code})')
                )
            else:
                skipped_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⊘ Skipped (exists): {college.name} ({college.code})')
                )
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Summary: Created {created_count} colleges, Skipped {skipped_count} existing')
        )
        self.stdout.write(f'Total colleges in database: {College.objects.count()}\n')
