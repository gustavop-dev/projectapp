"""
Seed the platform with demo data for development.

Creates:
  - 1 admin user (admin@projectapp.dev / Admin1234!)
  - 1 onboarded client (maria@techstartup.co / Client1234!)
  - 2 demo projects for the client

Usage:
  python manage.py seed_platform_data
  python manage.py seed_platform_data --flush   # removes previous seed data first
"""

import os
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Project, Requirement, UserProfile

User = get_user_model()

ADMIN_EMAIL = 'admin@projectapp.dev'
CLIENT_EMAIL = 'maria@techstartup.co'

ADMIN_PASSWORD = os.environ.get('SEED_ADMIN_PASSWORD', 'Admin1234!')
CLIENT_PASSWORD = os.environ.get('SEED_CLIENT_PASSWORD', 'Client1234!')


class Command(BaseCommand):
    help = 'Seed platform with one admin and one onboarded client for development.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Remove existing seed users before creating new ones.',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self._flush()

        admin_user = self._create_admin()
        client_user = self._create_client(created_by=admin_user)
        self._create_projects(client_user)

        self.stdout.write(self.style.SUCCESS('\nSeed data created successfully:'))
        self.stdout.write(f'  Admin  → {ADMIN_EMAIL} / (env SEED_ADMIN_PASSWORD or Admin1234!)')
        self.stdout.write(f'  Client → {CLIENT_EMAIL} / (env SEED_CLIENT_PASSWORD or Client1234!)')
        self.stdout.write('')

    def _flush(self):
        for email in [ADMIN_EMAIL, CLIENT_EMAIL]:
            user = User.objects.filter(email=email).first()
            if user:
                Project.objects.filter(client=user).delete()
                user.delete()
                self.stdout.write(f'  Deleted existing user: {email}')

    def _create_admin(self):
        if User.objects.filter(email=ADMIN_EMAIL).exists():
            self.stdout.write(f'  Admin already exists: {ADMIN_EMAIL}')
            return User.objects.get(email=ADMIN_EMAIL)

        user = User.objects.create_user(
            username=ADMIN_EMAIL,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            first_name='Gustavo',
            last_name='Pérez',
            is_staff=True,
        )
        UserProfile.objects.create(
            user=user,
            role=UserProfile.ROLE_ADMIN,
            is_onboarded=True,
            profile_completed=True,
            company_name='ProjectApp',
            phone='+57 310 555 0001',
        )
        self.stdout.write(self.style.SUCCESS(f'  Created admin: {ADMIN_EMAIL}'))
        return user

    def _create_client(self, created_by=None):
        if User.objects.filter(email=CLIENT_EMAIL).exists():
            self.stdout.write(f'  Client already exists: {CLIENT_EMAIL}')
            return User.objects.get(email=CLIENT_EMAIL)

        user = User.objects.create_user(
            username=CLIENT_EMAIL,
            email=CLIENT_EMAIL,
            password=CLIENT_PASSWORD,
            first_name='María',
            last_name='Torres',
        )
        UserProfile.objects.create(
            user=user,
            role=UserProfile.ROLE_CLIENT,
            is_onboarded=True,
            profile_completed=True,
            company_name='TechStartup Co.',
            phone='+57 300 123 4567',
            cedula='1020304050',
            date_of_birth='1992-06-15',
            gender=UserProfile.GENDER_FEMALE,
            education_level=UserProfile.EDUCATION_UNIVERSITY,
            created_by=created_by,
        )
        self.stdout.write(self.style.SUCCESS(f'  Created client: {CLIENT_EMAIL}'))
        return user

    def _create_projects(self, client_user):
        if Project.objects.filter(client=client_user).exists():
            self.stdout.write(f'  Projects already exist for {client_user.email}')
            return

        today = date.today()

        ecommerce_project = Project.objects.create(
            name='Plataforma E-commerce',
            description='Desarrollo de tienda en línea con catálogo de productos, carrito de compras, pasarela de pagos y panel de administración.',
            client=client_user,
            status=Project.STATUS_ACTIVE,
            progress=18,
            start_date=today - timedelta(days=30),
            estimated_end_date=today + timedelta(days=60),
        )

        Project.objects.create(
            name='App Móvil Inventarios',
            description='Aplicación móvil para gestión de inventario en tiempo real con lector de códigos de barras y sincronización con ERP.',
            client=client_user,
            status=Project.STATUS_PAUSED,
            progress=15,
            start_date=today - timedelta(days=10),
            estimated_end_date=today + timedelta(days=120),
        )

        self.stdout.write(self.style.SUCCESS(f'  Created 2 demo projects for {client_user.email}'))

        self._create_requirements(ecommerce_project)

    def _create_requirements(self, project):
        if Requirement.objects.filter(project=project).exists():
            self.stdout.write(f'  Requirements already exist for {project.name}')
            return

        reqs = [
            {'title': 'Diseño de la página principal', 'status': 'done', 'priority': 'high', 'module': 'Frontend', 'order': 0, 'estimated_hours': 16},
            {'title': 'Catálogo de productos con filtros', 'status': 'done', 'priority': 'high', 'module': 'Frontend', 'order': 1, 'estimated_hours': 24},
            {'title': 'Carrito de compras', 'status': 'in_review', 'priority': 'critical', 'module': 'Frontend', 'order': 0, 'estimated_hours': 20},
            {'title': 'Integración pasarela de pagos (Wompi)', 'status': 'in_progress', 'priority': 'critical', 'module': 'Backend', 'order': 0, 'estimated_hours': 32},
            {'title': 'Sistema de autenticación de usuarios', 'status': 'in_progress', 'priority': 'high', 'module': 'Backend', 'order': 1, 'estimated_hours': 12},
            {'title': 'Panel de administración de productos', 'status': 'in_review', 'priority': 'medium', 'module': 'Admin', 'order': 1, 'estimated_hours': 18},
            {'title': 'Notificaciones por email de pedidos', 'status': 'todo', 'priority': 'medium', 'module': 'Backend', 'order': 0, 'estimated_hours': 8},
            {'title': 'Sistema de cupones y descuentos', 'status': 'todo', 'priority': 'low', 'module': 'Backend', 'order': 1, 'estimated_hours': 14},
            {'title': 'Gestión de inventario', 'status': 'todo', 'priority': 'medium', 'module': 'Admin', 'order': 2, 'estimated_hours': 20},
            {'title': 'Reportes de ventas', 'status': 'todo', 'priority': 'low', 'module': 'Admin', 'order': 3, 'estimated_hours': 16},
            {'title': 'Optimización SEO del catálogo', 'status': 'todo', 'priority': 'low', 'module': 'Frontend', 'order': 4, 'estimated_hours': 10},
        ]

        for r in reqs:
            Requirement.objects.create(
                project=project,
                title=r['title'],
                status=r['status'],
                priority=r['priority'],
                module=r.get('module', ''),
                order=r.get('order', 0),
                estimated_hours=r.get('estimated_hours'),
            )

        self.stdout.write(self.style.SUCCESS(f'  Created {len(reqs)} requirements for {project.name}'))
