import random
import uuid

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from content.models import (
    BusinessProposal,
    ProposalChangeLog,
    ProposalSection,
    ProposalSectionView,
    ProposalShareLink,
    ProposalViewEvent,
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

REJECTION_REASONS = [
    'budget', 'timing', 'chose_competitor', 'scope_mismatch',
    'internal_changes', 'other',
]

REJECTION_COMMENTS = [
    'El presupuesto excede lo aprobado por dirección.',
    'Decidimos postergar el proyecto hasta el próximo trimestre.',
    'Fuimos con otra agencia que ofrecía un paquete más completo.',
    'El alcance no cubre lo que necesitamos actualmente.',
    'Hubo cambios internos y el proyecto ya no es prioridad.',
    '',
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Safari/17.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) Mobile/15E148',
    'Mozilla/5.0 (Linux; Android 14) Chrome/120.0 Mobile',
    'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) Safari/17.0',
]

SECTION_TYPES = [
    ('greeting', 'Saludo'),
    ('development_stages', 'Etapas de desarrollo'),
    ('investment', 'Inversión'),
    ('closing', 'Cierre'),
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
                data['responded_at'] = now - timedelta(days=random.randint(1, 4))
            elif status == 'rejected':
                data['sent_at'] = now - timedelta(days=random.randint(10, 20))
                data['first_viewed_at'] = now - timedelta(days=random.randint(5, 9))
                data['view_count'] = random.randint(1, 5)
                data['responded_at'] = now - timedelta(days=random.randint(1, 4))
                data['rejection_reason'] = random.choice(REJECTION_REASONS)
                data['rejection_comment'] = random.choice(REJECTION_COMMENTS)
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

            # --- Generate engagement data for non-draft proposals ---
            if status != 'draft':
                self._create_engagement_data(proposal, now)

            # Create default sections (groups now stored in content_json)
            lang = random.choice(['es', 'en']) if i % 3 == 0 else 'es'
            default_sections = ProposalService.get_default_sections(language=lang)
            for section_cfg in default_sections:
                if section_cfg['section_type'] == 'greeting':
                    section_cfg['content_json']['clientName'] = proposal.client_name
                if section_cfg['section_type'] == 'investment':
                    total = float(investment)
                    cur = currency
                    fmt = lambda n: f'${n:,.0f}'
                    section_cfg['content_json']['totalInvestment'] = fmt(total)
                    section_cfg['content_json']['currency'] = cur
                    section_cfg['content_json']['paymentOptions'] = [
                        {'label': f'40% al firmar el contrato ✍️', 'description': f'{fmt(total * 0.4)} {cur}'},
                        {'label': f'30% al aprobar el diseño final ✅', 'description': f'{fmt(total * 0.3)} {cur}'},
                        {'label': f'30% al desplegar el sitio web �', 'description': f'{fmt(total * 0.3)} {cur}'},
                    ]
                ProposalSection.objects.create(proposal=proposal, **section_cfg)

            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone: created {created} fake proposals '
                f'(statuses: {", ".join(STATUSES)}).'
            )
        )

    def _create_engagement_data(self, proposal, now):
        """Generate ViewEvents, SectionViews, ChangeLogs, and ShareLinks."""
        sent_at = proposal.sent_at or (now - timedelta(days=10))

        # --- ViewEvents + SectionViews ---
        num_sessions = proposal.view_count or random.randint(1, 4)
        ips = [f'192.168.1.{random.randint(10, 250)}' for _ in range(3)]
        for s in range(min(num_sessions, 6)):
            session_time = sent_at + timedelta(
                days=random.randint(0, 5),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            event = ProposalViewEvent.objects.create(
                proposal=proposal,
                session_id=uuid.uuid4().hex[:16],
                ip_address=random.choice(ips),
                user_agent=random.choice(USER_AGENTS),
            )
            event.viewed_at = session_time
            ProposalViewEvent.objects.filter(pk=event.pk).update(
                viewed_at=session_time,
            )

            for sect_type, sect_title in SECTION_TYPES:
                ProposalSectionView.objects.create(
                    view_event=event,
                    section_type=sect_type,
                    section_title=sect_title,
                    time_spent_seconds=round(random.uniform(3, 120), 1),
                    entered_at=session_time + timedelta(
                        seconds=random.randint(0, 300),
                    ),
                )

        # --- ChangeLogs ---
        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type='created',
            description=f'Proposal created for {proposal.client_name}.',
        )
        if proposal.sent_at:
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='sent',
                description=f'Proposal sent to {proposal.client_email}.',
            )
        if proposal.first_viewed_at:
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='viewed',
                description='Client opened the proposal for the first time.',
            )
        if proposal.status == 'accepted':
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='accepted',
                description='Client accepted the proposal.',
            )
        elif proposal.status == 'rejected':
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='rejected',
                description=(
                    f'Client rejected: {proposal.rejection_reason}.'
                ),
            )

        # --- ShareLinks (50% chance for viewed/accepted/rejected) ---
        if proposal.status in ('viewed', 'accepted', 'rejected'):
            if random.random() < 0.5:
                ProposalShareLink.objects.create(
                    proposal=proposal,
                    shared_by_name=proposal.client_name,
                    shared_by_email=proposal.client_email,
                    recipient_name=f'Socio de {proposal.client_name.split()[0]}',
                    recipient_email=f'socio.{proposal.client_name.split()[0].lower()}@example.com',
                    view_count=random.randint(0, 5),
                    first_viewed_at=(
                        now - timedelta(days=random.randint(1, 3))
                        if random.random() < 0.7 else None
                    ),
                )
