from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Create the first platform admin user with a UserProfile.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Admin email address')
        parser.add_argument('--password', required=True, help='Admin password')
        parser.add_argument('--first-name', default='Admin', help='First name')
        parser.add_argument('--last-name', default='', help='Last name')

    def handle(self, *args, **options):
        email = options['email'].lower().strip()
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            if hasattr(user, 'profile'):
                profile = user.profile
                if profile.role == UserProfile.ROLE_ADMIN:
                    self.stdout.write(self.style.WARNING(
                        f'Admin {email} already exists. Skipping.'
                    ))
                    return
                profile.role = UserProfile.ROLE_ADMIN
                profile.is_onboarded = True
                profile.save(update_fields=['role', 'is_onboarded'])
                self.stdout.write(self.style.SUCCESS(
                    f'Upgraded existing user {email} to platform admin.'
                ))
                return
            UserProfile.objects.create(
                user=user,
                role=UserProfile.ROLE_ADMIN,
                is_onboarded=True,
            )
            self.stdout.write(self.style.SUCCESS(
                f'Created admin profile for existing user {email}.'
            ))
            return

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
        )

        UserProfile.objects.create(
            user=user,
            role=UserProfile.ROLE_ADMIN,
            is_onboarded=True,
        )

        self.stdout.write(self.style.SUCCESS(
            f'Platform admin created: {email}'
        ))
