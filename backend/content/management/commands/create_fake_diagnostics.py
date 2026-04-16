"""Management command — create fake WebAppDiagnostic records for local / demo use."""

import random

from django.core.management.base import BaseCommand

from accounts.models import UserProfile
from accounts.services import proposal_client_service
from content.models import WebAppDiagnostic
from content.services import diagnostic_service


# ── Data pools ────────────────────────────────────────────────────────────

CLIENT_NAMES = [
    'María García', 'Carlos Rodríguez', 'John Smith', 'Ana López',
    'Pedro Martínez', 'Laura Sánchez', 'Diego Torres', 'Valentina Ríos',
    'Santiago Herrera', 'Camila Vargas', 'Andrés Moreno', 'Isabella Cruz',
]

CLIENT_COMPANIES = [
    'Acme Corp', 'Globex Industries', 'Initech Solutions',
    'TechVentures S.A.S.', 'Constructora del Norte', 'Clínica San Rafael',
    'Logística Andina', 'Pied Piper', 'Hooli', 'Aperture Science',
    '', '', '',  # some without company
]

DURATION_LABELS = ['3 días', '1 semana', '2 semanas', '1 mes']

_RADIOGRAPHY = {
    'small': {
        'stack': {
            'backend': {'name': 'Django', 'version': '4.2'},
            'frontend': {'name': 'Vue 3', 'version': '3.4'},
        },
        'migrations_count': 12,
        'entities_count': 8,
        'routes_total': 18,
        'routes_public': 5,
        'routes_protected': 13,
        'controllers_count': 10,
        'controllers_disconnected': 1,
        'frontend_routes_count': 9,
        'components_count': 14,
        'external_integrations': 1,
        'modules': ['Autenticación', 'Facturación', 'Reportes'],
        'test_files_count': 3,
        'test_coverage_label': 'Baja',
        'ci_files_count': 0,
        'docker_files_count': 0,
    },
    'medium': {
        'stack': {
            'backend': {'name': 'Node.js + Express', 'version': '18'},
            'frontend': {'name': 'React', 'version': '18.2'},
        },
        'migrations_count': 34,
        'entities_count': 28,
        'routes_total': 56,
        'routes_public': 14,
        'routes_protected': 42,
        'controllers_count': 31,
        'controllers_disconnected': 4,
        'frontend_routes_count': 24,
        'components_count': 52,
        'external_integrations': 4,
        'modules': [
            'Autenticación', 'Usuarios', 'Productos',
            'Facturación', 'Reportes', 'Notificaciones',
        ],
        'test_files_count': 18,
        'test_coverage_label': 'Media',
        'ci_files_count': 2,
        'docker_files_count': 1,
    },
    'large': {
        'stack': {
            'backend': {'name': 'Laravel', 'version': '10'},
            'frontend': {'name': 'Next.js', 'version': '14'},
        },
        'migrations_count': 89,
        'entities_count': 67,
        'routes_total': 134,
        'routes_public': 22,
        'routes_protected': 112,
        'controllers_count': 78,
        'controllers_disconnected': 11,
        'frontend_routes_count': 63,
        'components_count': 95,
        'external_integrations': 9,
        'modules': [
            'Autenticación', 'Usuarios', 'Roles y Permisos',
            'Productos', 'Inventario', 'Facturación',
            'Pagos', 'Reportes', 'Notificaciones', 'CRM',
        ],
        'test_files_count': 42,
        'test_coverage_label': 'Media-Alta',
        'ci_files_count': 3,
        'docker_files_count': 2,
    },
}

# Ordered list of statuses to walk through for --with-states
_STATE_PATHS = [
    [WebAppDiagnostic.Status.INITIAL_SENT],
    [WebAppDiagnostic.Status.INITIAL_SENT, WebAppDiagnostic.Status.IN_ANALYSIS],
    [WebAppDiagnostic.Status.INITIAL_SENT, WebAppDiagnostic.Status.IN_ANALYSIS,
     WebAppDiagnostic.Status.FINAL_SENT],
    [WebAppDiagnostic.Status.INITIAL_SENT, WebAppDiagnostic.Status.IN_ANALYSIS,
     WebAppDiagnostic.Status.FINAL_SENT, WebAppDiagnostic.Status.ACCEPTED],
    [WebAppDiagnostic.Status.INITIAL_SENT, WebAppDiagnostic.Status.IN_ANALYSIS,
     WebAppDiagnostic.Status.FINAL_SENT, WebAppDiagnostic.Status.REJECTED],
]


class Command(BaseCommand):
    help = 'Create fake WebAppDiagnostic records for local / demo use.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=5,
                            help='Number of diagnostics to create (default: 5)')
        parser.add_argument('--with-states', action='store_true',
                            help='Walk a subset through workflow transitions')
        parser.add_argument('--with-pricing', action='store_true',
                            help='Fill pricing and radiography data')
        parser.add_argument('--with-views', action='store_true',
                            help='Register random view counts')

    def handle(self, *args, **options):
        count = options['count']
        with_states = options['with_states']
        with_pricing = options['with_pricing']
        with_views = options['with_views']

        clients = list(UserProfile.objects.filter(role=UserProfile.ROLE_CLIENT)[:20])
        if not clients:
            self.stdout.write(self.style.WARNING(
                'No client profiles found — creating demo clients…'
            ))
            for i, name in enumerate(CLIENT_NAMES[:3]):
                email = f'demo_diag_{i}@temp.example.com'
                company = [c for c in CLIENT_COMPANIES if c][i % 7]
                profile = proposal_client_service.get_or_create_client_for_proposal(
                    name=name, email=email, phone='', company=company,
                )
                clients.append(profile)

        created = 0
        for _ in range(count):
            client = random.choice(clients)
            language = random.choices(['es', 'en'], weights=[80, 20])[0]
            diagnostic = diagnostic_service.create_diagnostic(
                client=client,
                language=language,
            )

            if with_pricing:
                currency = random.choice(['COP', 'USD'])
                amount = (
                    random.choice([1_500_000, 2_500_000, 4_000_000, 6_000_000, 8_000_000, 12_000_000])
                    if currency == 'COP'
                    else random.choice([3_000, 5_000, 8_000, 12_000, 20_000])
                )
                size = random.choice(['small', 'medium', 'large'])
                diagnostic.investment_amount = amount
                diagnostic.currency = currency
                diagnostic.payment_terms = {'initial_pct': 40, 'final_pct': 60}
                diagnostic.duration_label = random.choice(DURATION_LABELS)
                diagnostic.size_category = size
                diagnostic.radiography = _RADIOGRAPHY[size]
                diagnostic.save()

            if with_states:
                path = random.choice(_STATE_PATHS)
                try:
                    for status in path:
                        diagnostic_service.transition_status(diagnostic, status)
                except ValueError:
                    pass

            if with_views and diagnostic.status != WebAppDiagnostic.Status.DRAFT:
                for _ in range(random.randint(1, 8)):
                    diagnostic_service.register_view(diagnostic)

            created += 1
            self.stdout.write(self.style.SUCCESS(
                f'Created diagnostic #{diagnostic.id} '
                f'— {client} [{diagnostic.status}] [{diagnostic.language}]'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ {created} diagnostic(s) created.'
        ))
