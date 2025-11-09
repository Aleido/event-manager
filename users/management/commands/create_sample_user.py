from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates a sample user for development/testing purposes'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'test_user'
        password = 'Test@123'
        email = 'test_user@example.com' # Email is often required for User models

        if not User.objects.filter(username=username).exists():
            User.objects.create_user(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created sample user: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Sample user "{username}" already exists.'))