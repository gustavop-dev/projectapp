import random
import uuid

from copy import deepcopy
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from content.demo_technical_document import DEMO_TECHNICAL_DOCUMENT_JSON
from content.models import (
    BusinessProposal,
    ProposalAlert,
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

CLIENT_PHONES = [
    '+573001234567', '+573109876543', '+573205551234', '+573154443322',
    '+573187776655', '+14155551234', '+573001112233', '+573209998877',
    '', '', '',  # some without phone
]

PROJECT_TYPE_CHOICES = ['website', 'ecommerce', 'webapp', 'landing', 'redesign', 'other']
MARKET_TYPE_CHOICES = ['b2b', 'b2c', 'saas', 'retail', 'services', 'health', 'education', 'real_estate', 'other']

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

# Aligned with ProposalService.get_hardcoded_defaults('es') for synthetic ProposalSectionView rows.
SECTION_TYPES = [
    (s['section_type'], s['title'])
    for s in ProposalService.get_hardcoded_defaults(language='es')
]

ALERT_TYPES = [
    'reminder', 'followup', 'call', 'meeting', 'custom',
    'discount_suggestion', 'post_expiration_visit',
]

STATUSES = list(BusinessProposal.Status.values)


class Command(BaseCommand):
    help = (
        'Create fake business proposals with all default sections; technical_document uses '
        'demo content for dev (public technical mode + panel JSON).'
    )

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

            lang = random.choices(['es', 'en'], weights=[0.7, 0.3])[0]

            chosen_project_type = random.choice(PROJECT_TYPE_CHOICES)
            chosen_market_type = random.choice(MARKET_TYPE_CHOICES)

            data = {
                'title': f'Propuesta {project_type} — {client_name.split()[0]}',
                'client_name': client_name,
                'client_email': f'{client_name.split()[0].lower()}@example.com',
                'client_phone': random.choice(CLIENT_PHONES),
                'total_investment': investment,
                'currency': currency,
                'status': status,
                'discount_percent': discount,
                'expires_at': now + timedelta(days=random.randint(7, 45)),
                'language': lang,
                'project_type': chosen_project_type,
                'market_type': chosen_market_type,
            }

            # Fill custom text when type is 'other'
            if chosen_project_type == 'other':
                data['project_type_custom'] = random.choice([
                    'Portal interno corporativo',
                    'Herramienta de gestión de inventarios',
                    'Sistema de turnos médicos',
                    'Plataforma de crowdfunding',
                ])
            if chosen_market_type == 'other':
                data['market_type_custom'] = random.choice([
                    'Agroindustria',
                    'Logística y transporte',
                    'Turismo y hotelería',
                    'ONG y fundaciones',
                ])

            # ~20% of non-draft proposals have automations paused
            if status != 'draft' and random.random() < 0.2:
                data['automations_paused'] = True

            # Set realistic lifecycle fields per status
            if status == 'sent':
                data['sent_at'] = now - timedelta(days=random.randint(1, 5))
                data['last_activity_at'] = data['sent_at']
            elif status == 'viewed':
                data['sent_at'] = now - timedelta(days=random.randint(5, 10))
                data['first_viewed_at'] = now - timedelta(days=random.randint(1, 4))
                data['view_count'] = random.randint(1, 8)
                data['last_activity_at'] = data['first_viewed_at']
            elif status == 'accepted':
                data['sent_at'] = now - timedelta(days=random.randint(10, 20))
                data['first_viewed_at'] = now - timedelta(days=random.randint(5, 9))
                data['view_count'] = random.randint(3, 15)
                data['responded_at'] = now - timedelta(days=random.randint(1, 4))
                data['last_activity_at'] = data['responded_at']
            elif status == 'rejected':
                data['sent_at'] = now - timedelta(days=random.randint(10, 20))
                data['first_viewed_at'] = now - timedelta(days=random.randint(5, 9))
                data['view_count'] = random.randint(1, 5)
                data['responded_at'] = now - timedelta(days=random.randint(1, 4))
                data['rejection_reason'] = random.choice(REJECTION_REASONS)
                data['rejection_comment'] = random.choice(REJECTION_COMMENTS)
                data['last_activity_at'] = data['responded_at']
            elif status == 'negotiating':
                data['sent_at'] = now - timedelta(days=random.randint(5, 15))
                data['first_viewed_at'] = now - timedelta(days=random.randint(2, 4))
                data['view_count'] = random.randint(2, 10)
                data['responded_at'] = now - timedelta(days=random.randint(0, 2))
                data['last_activity_at'] = data['responded_at']
            elif status == 'expired':
                data['sent_at'] = now - timedelta(days=random.randint(30, 60))
                data['first_viewed_at'] = now - timedelta(days=random.randint(20, 29))
                data['view_count'] = random.randint(0, 3)
                data['expires_at'] = now - timedelta(days=random.randint(1, 10))
                data['last_activity_at'] = data.get('first_viewed_at') or data['sent_at']

            proposal = BusinessProposal.objects.create(**data)
            self.stdout.write(
                self.style.SUCCESS(
                    f'[{status:>8}] {proposal}'
                )
            )

            # --- Generate engagement data for non-draft proposals ---
            if status != 'draft':
                self._create_engagement_data(proposal, now)

            # --- Generate alerts for some proposals ---
            if status in ('sent', 'viewed', 'rejected', 'expired') and random.random() < 0.4:
                self._create_alerts(proposal, now)

            # --- Generate calculator interaction logs ---
            if status in ('viewed', 'accepted', 'negotiating') and random.random() < 0.5:
                self._create_calculator_logs(proposal)

            # --- Generate seller activity logs ---
            if status in ('viewed', 'accepted', 'negotiating', 'rejected') and random.random() < 0.6:
                self._create_seller_activity_logs(proposal, now)

            # Create default sections (groups now stored in content_json)
            default_sections = ProposalService.get_default_sections(language=lang)
            for section_cfg in default_sections:
                cfg = deepcopy(section_cfg)
                if cfg['section_type'] == 'greeting':
                    cfg['content_json']['clientName'] = proposal.client_name
                if cfg['section_type'] == 'investment':
                    total = float(investment)
                    cur = currency
                    fmt = lambda n: f'${n:,.0f}'
                    cfg['content_json']['totalInvestment'] = fmt(total)
                    cfg['content_json']['currency'] = cur
                    cfg['content_json']['paymentOptions'] = [
                        {'label': f'40% al firmar el contrato ✍️', 'description': f'{fmt(total * 0.4)} {cur}'},
                        {'label': f'30% al aprobar el diseño final ✅', 'description': f'{fmt(total * 0.3)} {cur}'},
                        {'label': f'30% al desplegar el sitio web 🚀', 'description': f'{fmt(total * 0.3)} {cur}'},
                    ]
                if cfg['section_type'] == 'technical_document':
                    cfg['content_json'] = deepcopy(DEMO_TECHNICAL_DOCUMENT_JSON)
                ProposalSection.objects.create(proposal=proposal, **cfg)

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
        elif proposal.status == 'negotiating':
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='negotiating',
                description='Client accepted with changes — negotiation started.',
            )
        elif proposal.status == 'expired':
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='expired',
                description='Proposal expired without a response.',
            )

        # Sprinkle additional lifecycle logs for realism
        if proposal.status in ('viewed', 'accepted', 'negotiating') and random.random() < 0.3:
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='commented',
                description=random.choice([
                    'Cliente dejó un comentario: "Me interesa pero tengo dudas sobre el cronograma."',
                    'Comentario del cliente: "¿Pueden incluir soporte post-lanzamiento?"',
                    'Nota del cliente: "Necesito consultarlo con mi socio."',
                ]),
            )
        if proposal.status in ('sent', 'viewed') and random.random() < 0.15:
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='resent',
                description='Proposal re-sent to the client after updates.',
            )
        if random.random() < 0.1:
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='duplicated',
                description='Proposal duplicated as a new draft.',
            )
        if proposal.status in ('rejected', 'expired') and random.random() < 0.2:
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='reengagement',
                description=random.choice([
                    'Reengagement email sent — client showed renewed interest.',
                    'Client revisited proposal after rejection. Reengagement triggered.',
                ]),
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

    def _create_alerts(self, proposal, now):
        """Generate ProposalAlert records for the proposal."""
        alert_type = random.choice(ALERT_TYPES)
        messages = {
            'reminder': f'Recordatorio: hacer seguimiento a {proposal.client_name} esta semana.',
            'followup': f'Seguimiento pendiente con {proposal.client_name} sobre la propuesta.',
            'call': f'Llamar a {proposal.client_name} para revisar estado de la propuesta.',
            'meeting': f'Agendar reunión con {proposal.client_name} para revisión de alcance.',
            'custom': f'Nota personalizada sobre {proposal.client_name}.',
            'discount_suggestion': f'{proposal.client_name} ha visitado la propuesta varias veces. Considerar ofrecer descuento.',
            'post_expiration_visit': f'{proposal.client_name} abrió la propuesta expirada. Señal de alto interés.',
        }
        ProposalAlert.objects.create(
            proposal=proposal,
            alert_type=alert_type,
            message=messages.get(alert_type, 'Alert'),
            alert_date=now - timedelta(days=random.randint(0, 5)),
        )

    def _create_calculator_logs(self, proposal):
        """Generate calculator interaction change logs."""
        import json
        modules = [
            'pwa_module', 'ai_module', 'reports_alerts_module',
            'kpi_dashboard_module', 'email_marketing_module',
            'conversion_tracking_module', 'i18n_module', 'gift_cards_module',
        ]
        selected = random.sample(modules, k=random.randint(2, 4))
        # kpi_dashboard_module is free and selected by default
        if 'kpi_dashboard_module' not in selected:
            selected.append('kpi_dashboard_module')
        deselected = [m for m in modules if m not in selected]

        # Confirmed interaction
        ProposalChangeLog.objects.create(
            proposal=proposal,
            change_type='calc_confirmed',
            description=json.dumps({
                'selected': selected,
                'deselected': deselected,
                'total': float(proposal.total_investment),
            }),
        )

        # 30% chance of also having an abandoned interaction before confirming
        if random.random() < 0.3:
            ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type='calc_abandoned',
                description=json.dumps({
                    'selected': modules,
                    'deselected': [],
                    'total': float(proposal.total_investment),
                }),
            )

    def _create_seller_activity_logs(self, proposal, now):
        """Generate seller activity change logs (call, meeting, followup, note)."""
        activity_types = ['call', 'meeting', 'followup', 'note']
        descriptions = {
            'call': [
                'Llamada de seguimiento. Cliente interesado, pide más info sobre módulo PWA.',
                'Llamada inicial para presentar la propuesta. Buena recepción.',
                'Cliente solicitó llamada para aclarar dudas sobre el cronograma.',
                'Seguimiento telefónico. Pendiente aprobación de presupuesto interno.',
            ],
            'meeting': [
                'Reunión virtual para revisión de requerimientos funcionales.',
                'Demo del dashboard de KPIs al equipo directivo del cliente.',
                'Reunión presencial. Cliente quiere agregar módulo de email marketing.',
            ],
            'followup': [
                'Email de seguimiento con resumen de la reunión.',
                'Envío de caso de éxito similar al sector del cliente.',
                'Seguimiento post-demo. Cliente evaluando internamente.',
            ],
            'note': [
                'Cliente mencionó que compara con otra agencia. Reforzar propuesta de valor.',
                'Contacto del socio del cliente pidió información adicional.',
                'Presupuesto aprobado internamente, esperando firma.',
            ],
        }
        num_activities = random.randint(1, 3)
        ref_date = proposal.sent_at or (now - timedelta(days=10))
        for _ in range(num_activities):
            act_type = random.choice(activity_types)
            desc = random.choice(descriptions[act_type])
            activity_date = ref_date + timedelta(
                days=random.randint(1, 10),
                hours=random.randint(8, 18),
            )
            log = ProposalChangeLog.objects.create(
                proposal=proposal,
                change_type=act_type,
                description=desc,
            )
            ProposalChangeLog.objects.filter(pk=log.pk).update(
                created_at=activity_date,
            )
