from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from content.models import Task

User = get_user_model()

TASKS = [
    {
        'title': 'Revisar sistema de emails automáticos',
        'description': 'Verificar que todos los correos de propuestas se envían correctamente en producción.',
        'status': Task.Status.TODO,
        'priority': Task.Priority.HIGH,
        'due_days': 3,
    },
    {
        'title': 'Actualizar README con instrucciones de deploy',
        'description': '',
        'status': Task.Status.TODO,
        'priority': Task.Priority.LOW,
        'due_days': None,
    },
    {
        'title': 'Implementar paginación en listado de propuestas',
        'description': 'El listado ya tiene más de 50 propuestas y se está volviendo lento.',
        'status': Task.Status.IN_PROGRESS,
        'priority': Task.Priority.MEDIUM,
        'due_days': 7,
    },
    {
        'title': 'Migrar base de datos a MySQL 8.4',
        'description': 'Actualización mayor de versión. Requiere backup previo y ventana de mantenimiento.',
        'status': Task.Status.BLOCKED,
        'priority': Task.Priority.HIGH,
        'due_days': 14,
    },
    {
        'title': 'Configurar CDN para assets estáticos',
        'description': 'Cloudflare o similar para reducir latencia de archivos estáticos en Colombia.',
        'status': Task.Status.DONE,
        'priority': Task.Priority.MEDIUM,
        'due_days': None,
    },
]


class Command(BaseCommand):
    help = 'Seed a handful of demo Kanban tasks for local development.'

    def handle(self, *args, **options):
        if Task.objects.exists():
            self.stdout.write(self.style.WARNING('Tasks already exist — skipped.'))
            return

        today = timezone.localdate()
        admin = User.objects.filter(is_staff=True).first()

        for position, spec in enumerate(TASKS):
            due = (today + timedelta(days=spec['due_days'])) if spec['due_days'] else None
            Task.objects.create(
                title=spec['title'],
                description=spec['description'],
                status=spec['status'],
                priority=spec['priority'],
                assignee=admin,
                due_date=due,
                position=position,
            )

        self.stdout.write(self.style.SUCCESS(f'{len(TASKS)} fake tasks created.'))
