from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Deletes users who are marked as inactive (is_active=False).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run the command without actually deleting any users.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        User = get_user_model()

        # Filter inactive users
        # Exclude superusers and staff to prevent accidental deletion of important accounts
        inactive_users = User.objects.filter(is_active=False).exclude(is_superuser=True).exclude(is_staff=True)
        count = inactive_users.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No inactive users found to delete.'))
            return

        self.stdout.write(f"Found {count} inactive users.")

        if dry_run:
            self.stdout.write(self.style.WARNING(f"DRY RUN: {count} users found but NOT deleted."))
            for user in inactive_users:
                 self.stdout.write(f" - {user.email} (ID: {user.id})")
        else:
            deleted_count, _ = inactive_users.delete()
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted {deleted_count} inactive users."))
