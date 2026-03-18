from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import UserProfile

User = get_user_model()

DEMO_CLIENTS = [
    {
        'email': 'cliente1@demo.com',
        'first_name': 'María',
        'last_name': 'García',
        'company_name': 'TechStart SAS',
        'phone': '+57 300 111 2222',
        'is_onboarded': True,
        'is_active': True,
    },
    {
        'email': 'cliente2@demo.com',
        'first_name': 'Carlos',
        'last_name': 'Rodríguez',
        'company_name': 'Innova Digital',
        'phone': '+57 310 333 4444',
        'is_onboarded': True,
        'is_active': True,
    },
    {
        'email': 'cliente3@demo.com',
        'first_name': 'Ana',
        'last_name': 'Martínez',
        'company_name': 'GreenFood Co',
        'phone': '',
        'is_onboarded': False,
        'is_active': True,
    },
    {
        'email': 'cliente4@demo.com',
        'first_name': 'Jorge',
        'last_name': 'López',
        'company_name': 'LogiTrans',
        'phone': '+57 320 555 6666',
        'is_onboarded': True,
        'is_active': False,
    },
]


class Command(BaseCommand):
    help = 'Seed demo client accounts for development/testing.'

    def handle(self, *args, **options):
        admin = User.objects.filter(profile__role=UserProfile.ROLE_ADMIN).first()

        created = 0
        skipped = 0

        for client_data in DEMO_CLIENTS:
            email = client_data['email']
            if User.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f'  Skipped {email} (already exists)'))
                skipped += 1
                continue

            user = User.objects.create_user(
                username=email,
                email=email,
                password='demo1234',
                first_name=client_data['first_name'],
                last_name=client_data['last_name'],
                is_active=client_data['is_active'],
            )

            UserProfile.objects.create(
                user=user,
                role=UserProfile.ROLE_CLIENT,
                is_onboarded=client_data['is_onboarded'],
                company_name=client_data['company_name'],
                phone=client_data['phone'],
                created_by=admin,
            )

            status_label = 'onboarded' if client_data['is_onboarded'] else 'pending'
            if not client_data['is_active']:
                status_label = 'inactive'

            self.stdout.write(self.style.SUCCESS(
                f'  Created {email} ({client_data["company_name"]}) [{status_label}]'
            ))
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone: {created} created, {skipped} skipped.'
        ))
