"""
Create additional demo client users for admin CRM / platform tests.

Covers: onboarded vs pending, active vs inactive, empty phone, long company names.
Password: env DEMO_CLIENT_PASSWORD or default "demo1234".

Usage:
  python manage.py seed_demo_clients
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import UserProfile

User = get_user_model()

DEMO_PASSWORD = os.environ.get('DEMO_CLIENT_PASSWORD', 'demo1234')

DEMO_CLIENTS = [
    {
        'email': 'cliente1@demo.com',
        'first_name': 'María',
        'last_name': 'García',
        'company_name': 'TechStart SAS',
        'phone': '+57 300 111 2222',
        'cedula': '1012345678',
        'is_onboarded': True,
        'profile_completed': True,
        'is_active': True,
    },
    {
        'email': 'cliente2@demo.com',
        'first_name': 'Carlos',
        'last_name': 'Rodríguez',
        'company_name': 'Innova Digital',
        'phone': '+57 310 333 4444',
        'cedula': '80765432',
        'is_onboarded': True,
        'profile_completed': True,
        'is_active': True,
    },
    {
        'email': 'cliente3@demo.com',
        'first_name': 'Ana',
        'last_name': 'Martínez',
        'company_name': 'GreenFood Co',
        'phone': '',
        'cedula': '',
        'is_onboarded': False,
        'profile_completed': False,
        'is_active': True,
    },
    {
        'email': 'cliente4@demo.com',
        'first_name': 'Jorge',
        'last_name': 'López',
        'company_name': 'LogiTrans',
        'phone': '+57 320 555 6666',
        'cedula': '944556677',
        'is_onboarded': True,
        'profile_completed': True,
        'is_active': False,
    },
    {
        'email': 'cliente5@demo.com',
        'first_name': 'Laura',
        'last_name': 'Benítez',
        'company_name': 'Agencia Creativa del Pacífico — Marketing & Data',
        'phone': '+57 301 999 0000',
        'cedula': '1122334455',
        'is_onboarded': True,
        'profile_completed': False,
        'is_active': True,
    },
    {
        'email': 'pending.invite@demo.com',
        'first_name': 'Invited',
        'last_name': 'User',
        'company_name': 'Future Client LLC',
        'phone': '+1 305 555 0100',
        'cedula': '',
        'is_onboarded': False,
        'profile_completed': False,
        'is_active': True,
    },
]


class Command(BaseCommand):
    help = 'Seed demo client accounts for development and CRM UI tests.'

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
                password=DEMO_PASSWORD,
                first_name=client_data['first_name'],
                last_name=client_data['last_name'],
                is_active=client_data['is_active'],
            )

            UserProfile.objects.create(
                user=user,
                role=UserProfile.ROLE_CLIENT,
                is_onboarded=client_data['is_onboarded'],
                profile_completed=client_data['profile_completed'],
                company_name=client_data['company_name'],
                phone=client_data['phone'],
                cedula=client_data.get('cedula', ''),
                created_by=admin,
            )

            if not client_data['is_active']:
                status_label = 'inactive'
            elif not client_data['is_onboarded']:
                status_label = 'pending_onboarding'
            elif not client_data['profile_completed']:
                status_label = 'onboarded_profile_incomplete'
            else:
                status_label = 'onboarded'

            self.stdout.write(self.style.SUCCESS(
                f'  Created {email} ({client_data["company_name"]}) [{status_label}]',
            ))
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nDone: {created} created, {skipped} skipped. Password: env DEMO_CLIENT_PASSWORD or {DEMO_PASSWORD!r}',
        ))
