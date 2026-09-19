from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from monitoring.models import Case, CaseActivity, Report, Resource, Source


class Command(BaseCommand):
    help = 'Crear ejemplos de monitoreo exclusivamente en desarrollo.'

    def handle(self, *args, **options):
        if not getattr(settings, 'FAKE_DATA_ALLOWED', False) or getattr(settings, 'IS_PRODUCTION', False):
            raise CommandError('Los datos ficticios no están permitidos en este entorno.')
        server, _ = Resource.objects.get_or_create(key='demo-server', defaults={'name': 'Servidor de demostración', 'kind': 'server'})
        project, _ = Resource.objects.get_or_create(key='demo-project', defaults={'name': 'Proyecto de demostración', 'kind': 'project', 'server': server})
        now = timezone.now()
        for resource in [server, project]:
            source, _ = Source.objects.get_or_create(resource=resource, key='demo', defaults={'name': 'Monitor de demostración', 'last_seen_at': now})
            for index in range(30):
                case, created = Case.objects.get_or_create(source=source, fingerprint_hash=f'{index:064x}', defaults={'fingerprint': f'demo-{index}', 'title': f'Ejemplo de observación {index + 1}', 'severity': ['info', 'warning', 'critical'][index % 3], 'state': ['pending', 'reviewing', 'resolved'][index % 3], 'condition': 'recovered' if index % 2 else 'active', 'first_seen_at': now - timedelta(days=3), 'last_seen_at': now - timedelta(hours=index), 'closed_at': now if index % 3 == 2 else None, 'detections': index + 1, 'evidence': {'metric': 'duration', 'value': 650, 'unit': 'ms'}})
                if created:
                    CaseActivity.objects.create(case=case, kind='note', actor_name='Demo', text='Ejemplo para validar el seguimiento manual.')
            Report.objects.get_or_create(source=source, title='Reporte de demostración', defaults={'observed_at': now, 'text': 'Reporte informativo de ejemplo; sin incidentes nuevos.'})
        self.stdout.write('Datos de monitoreo disponibles.')
