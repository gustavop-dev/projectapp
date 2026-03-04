import random

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from content.models import (
    BusinessProposal,
    ProposalRequirementGroup,
    ProposalRequirementItem,
    ProposalSection,
)
from content.services.proposal_service import ProposalService

# Pool of realistic client data for random selection
CLIENT_NAMES = [
    'María García', 'Carlos Rodríguez', 'John Smith', 'Ana López',
    'Pedro Martínez', 'Laura Sánchez', 'Diego Torres', 'Valentina Ríos',
    'Santiago Herrera', 'Camila Vargas', 'Andrés Moreno', 'Isabella Cruz',
    'Felipe Ramírez', 'Daniela Ortiz', 'Mateo Gutiérrez', 'Sofía Mendoza',
    'Julián Castro', 'Paula Jiménez', 'Nicolás Rojas', 'Mariana Díaz',
]

PROJECT_TYPES = [
    ('Landing Profesional', 3500000, 'COP'),
    ('E-Commerce — Tienda Online', 8500000, 'COP'),
    ('SaaS Dashboard', 5000, 'USD'),
    ('Portafolio Creativo', 2800000, 'COP'),
    ('Plataforma Educativa', 12000000, 'COP'),
    ('App Corporativa', 7500, 'USD'),
    ('Blog + SEO', 1900000, 'COP'),
    ('Marketplace MVP', 15000000, 'COP'),
    ('Sistema de Reservas', 4200000, 'COP'),
    ('Web Institucional', 3000000, 'COP'),
]

STATUSES = list(BusinessProposal.Status.values)


class Command(BaseCommand):
    help = 'Create fake business proposals with sections and requirement groups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', type=int, default=10,
            help='Number of proposals to create (default: 10)',
        )

    def handle(self, *args, **options):
        count = options['count']
        now = timezone.now()

        created = 0
        for i in range(count):
            status = STATUSES[i % len(STATUSES)]
            client_name = CLIENT_NAMES[i % len(CLIENT_NAMES)]
            project_type, investment, currency = PROJECT_TYPES[i % len(PROJECT_TYPES)]
            discount = random.choice([0, 10, 15, 20, 25])

            data = {
                'title': f'Propuesta {project_type} — {client_name.split()[0]}',
                'client_name': client_name,
                'client_email': f'{client_name.split()[0].lower()}@example.com',
                'total_investment': investment,
                'currency': currency,
                'status': status,
                'discount_percent': discount,
                'expires_at': now + timedelta(days=random.randint(7, 45)),
            }

            # Set realistic lifecycle fields per status
            if status == 'sent':
                data['sent_at'] = now - timedelta(days=random.randint(1, 5))
            elif status == 'viewed':
                data['sent_at'] = now - timedelta(days=random.randint(5, 10))
                data['first_viewed_at'] = now - timedelta(days=random.randint(1, 4))
                data['view_count'] = random.randint(1, 8)
            elif status == 'accepted':
                data['sent_at'] = now - timedelta(days=random.randint(10, 20))
                data['first_viewed_at'] = now - timedelta(days=random.randint(5, 9))
                data['view_count'] = random.randint(3, 15)
            elif status == 'rejected':
                data['sent_at'] = now - timedelta(days=random.randint(10, 20))
                data['first_viewed_at'] = now - timedelta(days=random.randint(5, 9))
                data['view_count'] = random.randint(1, 5)
            elif status == 'expired':
                data['sent_at'] = now - timedelta(days=random.randint(30, 60))
                data['first_viewed_at'] = now - timedelta(days=random.randint(20, 29))
                data['view_count'] = random.randint(0, 3)
                data['expires_at'] = now - timedelta(days=random.randint(1, 10))

            proposal = BusinessProposal.objects.create(**data)
            self.stdout.write(
                self.style.SUCCESS(
                    f'[{status:>8}] {proposal}'
                )
            )

            # Create default sections
            default_sections = ProposalService.get_default_sections()
            for section_cfg in default_sections:
                if section_cfg['section_type'] == 'greeting':
                    section_cfg['content_json']['clientName'] = proposal.client_name
                ProposalSection.objects.create(proposal=proposal, **section_cfg)

            # Create sample requirement groups + items
            views_group = ProposalRequirementGroup.objects.create(
                proposal=proposal, group_id='views',
                title='🖥️ Vistas',
                description='Páginas principales del sitio web.', order=0,
            )
            ProposalRequirementItem.objects.create(
                group=views_group, item_id='home', icon='🏠',
                name='Página Principal', description='Landing principal del sitio.', order=0,
            )
            ProposalRequirementItem.objects.create(
                group=views_group, item_id='contact', icon='📧',
                name='Página de Contacto', description='Formulario de contacto.', order=1,
            )

            components_group = ProposalRequirementGroup.objects.create(
                proposal=proposal, group_id='components',
                title='🧩 Componentes',
                description='Componentes reutilizables.', order=1,
            )
            ProposalRequirementItem.objects.create(
                group=components_group, item_id='navbar', icon='📌',
                name='Navbar', description='Barra de navegación responsiva.', order=0,
            )
            ProposalRequirementItem.objects.create(
                group=components_group, item_id='footer', icon='📎',
                name='Footer', description='Pie de página con enlaces y redes sociales.', order=1,
            )

            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone: created {created} fake proposals '
                f'(statuses: {", ".join(STATUSES)}).'
            )
        )
