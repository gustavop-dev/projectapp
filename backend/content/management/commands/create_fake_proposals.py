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


class Command(BaseCommand):
    help = 'Create fake business proposals with sections and requirement groups'

    def handle(self, *args, **options):
        proposals_data = [
            {
                'title': 'Propuesta Desarrollo Web — Landing Profesional',
                'client_name': 'María García',
                'client_email': 'maria@example.com',
                'total_investment': 3500000,
                'currency': 'COP',
                'status': 'draft',
                'expires_at': timezone.now() + timedelta(days=30),
            },
            {
                'title': 'Propuesta E-Commerce — Tienda Online',
                'client_name': 'Carlos Rodríguez',
                'client_email': 'carlos@example.com',
                'total_investment': 8500000,
                'currency': 'COP',
                'status': 'sent',
                'sent_at': timezone.now() - timedelta(days=3),
                'expires_at': timezone.now() + timedelta(days=27),
            },
            {
                'title': 'Web App Proposal — SaaS Dashboard',
                'client_name': 'John Smith',
                'client_email': 'john@example.com',
                'total_investment': 5000,
                'currency': 'USD',
                'status': 'viewed',
                'sent_at': timezone.now() - timedelta(days=7),
                'first_viewed_at': timezone.now() - timedelta(days=5),
                'view_count': 4,
                'expires_at': timezone.now() + timedelta(days=23),
            },
        ]

        for data in proposals_data:
            proposal = BusinessProposal.objects.create(**data)
            self.stdout.write(
                self.style.SUCCESS(f'Created proposal: {proposal}')
            )

            # Create default sections
            default_sections = ProposalService.get_default_sections()
            for section_cfg in default_sections:
                # Inject client_name into greeting
                if section_cfg['section_type'] == 'greeting':
                    section_cfg['content_json']['clientName'] = proposal.client_name
                ProposalSection.objects.create(proposal=proposal, **section_cfg)

            self.stdout.write(
                f'  → Created {len(default_sections)} sections'
            )

            # Create sample requirement groups + items for each proposal
            views_group = ProposalRequirementGroup.objects.create(
                proposal=proposal,
                group_id='views',
                title='🖥️ Vistas',
                description='Páginas principales del sitio web.',
                order=0,
            )
            ProposalRequirementItem.objects.create(
                group=views_group, item_id='home', icon='🏠',
                name='Página Principal', description='Landing principal del sitio.',
                order=0,
            )
            ProposalRequirementItem.objects.create(
                group=views_group, item_id='contact', icon='📧',
                name='Página de Contacto', description='Formulario de contacto.',
                order=1,
            )

            components_group = ProposalRequirementGroup.objects.create(
                proposal=proposal,
                group_id='components',
                title='🧩 Componentes',
                description='Componentes reutilizables.',
                order=1,
            )
            ProposalRequirementItem.objects.create(
                group=components_group, item_id='navbar', icon='📌',
                name='Navbar', description='Barra de navegación responsiva.',
                order=0,
            )
            ProposalRequirementItem.objects.create(
                group=components_group, item_id='footer', icon='📎',
                name='Footer', description='Pie de página con enlaces y redes sociales.',
                order=1,
            )

            self.stdout.write(
                f'  → Created 2 requirement groups with 4 items'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone: created {len(proposals_data)} fake proposals.'
            )
        )
