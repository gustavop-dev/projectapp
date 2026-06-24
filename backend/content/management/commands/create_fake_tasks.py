import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from content.models import Task, TaskAlert, TaskComment

User = get_user_model()

# Curated seed tasks kept verbatim so the default board reads naturally.
BASE_TASKS = [
    {
        'title': 'Revisar sistema de emails automáticos',
        'description': 'Verificar que todos los correos de propuestas se envían correctamente en producción.',
        'status': Task.Status.TODO, 'priority': Task.Priority.HIGH, 'due_days': 3,
    },
    {
        'title': 'Actualizar README con instrucciones de deploy',
        'description': '', 'status': Task.Status.TODO, 'priority': Task.Priority.LOW, 'due_days': None,
    },
    {
        'title': 'Implementar paginación en listado de propuestas',
        'description': 'El listado ya tiene más de 50 propuestas y se está volviendo lento.',
        'status': Task.Status.IN_PROGRESS, 'priority': Task.Priority.MEDIUM, 'due_days': 7,
    },
    {
        'title': 'Migrar base de datos a MySQL 8.4',
        'description': 'Actualización mayor de versión. Requiere backup previo y ventana de mantenimiento.',
        'status': Task.Status.BLOCKED, 'priority': Task.Priority.HIGH, 'due_days': 14,
    },
    {
        'title': 'Configurar CDN para assets estáticos',
        'description': 'Cloudflare o similar para reducir latencia de archivos estáticos en Colombia.',
        'status': Task.Status.DONE, 'priority': Task.Priority.MEDIUM, 'due_days': None,
    },
]

# Pool to scale beyond the curated set, distributed across boards.
EXTRA_TITLES = [
    'Optimizar consultas N+1 en el panel de clientes',
    'Diseñar plantilla de cuenta de cobro en PDF',
    'Agregar filtros guardados al mapa de vistas',
    'Escribir pruebas E2E del flujo de onboarding',
    'Documentar la API de la plataforma',
    'Mejorar accesibilidad del checkout',
    'Revisar alertas de propuestas zombie',
    'Configurar backups automáticos de la base de datos',
    'Integrar webhook de Wompi para suscripciones',
    'Refactorizar el servicio de generación de contratos',
    'Auditar dependencias del frontend',
    'Crear dashboard de métricas de hosting',
    'Limpiar datos de prueba antiguos',
    'Añadir modo oscuro al portal del cliente',
    'Revisar tiempos de carga del blog',
]

COMMENTS = [
    'Avancé con la parte inicial, falta validar en staging.',
    'Bloqueado a la espera de credenciales del cliente.',
    '¿Podemos priorizar esto para el próximo sprint?',
    'Listo y verificado en producción.',
    'Dejé notas en el documento técnico del proyecto.',
]


class Command(BaseCommand):
    help = 'Seed demo Kanban tasks (with alerts and comments) for local development.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', type=int, default=len(BASE_TASKS),
            help=f'Total number of tasks to create (default: {len(BASE_TASKS)}).',
        )

    def handle(self, *args, **options):
        count = max(len(BASE_TASKS), options['count'])

        if Task.objects.count() >= count:
            self.stdout.write(self.style.WARNING(
                f'{Task.objects.count()} tasks already exist — skipped.'))
            return

        rng = random.Random(11)
        today = timezone.localdate()
        admin = User.objects.filter(is_staff=True).first()
        statuses = list(Task.Status)
        priorities = list(Task.Priority)
        boards = list(Task.BoardType)

        specs = list(BASE_TASKS)
        for i in range(len(BASE_TASKS), count):
            title = EXTRA_TITLES[(i - len(BASE_TASKS)) % len(EXTRA_TITLES)]
            cycle = (i - len(BASE_TASKS)) // len(EXTRA_TITLES)
            specs.append({
                'title': f'{title}{" (" + str(cycle + 1) + ")" if cycle else ""}',
                'description': 'Tarea generada para poblar el tablero de desarrollo.',
                'status': rng.choice(statuses),
                'priority': rng.choice(priorities),
                'due_days': rng.choice([None, 2, 5, 10, 20, -3]),
            })

        created = 0
        for position, spec in enumerate(specs):
            due = (today + timedelta(days=spec['due_days'])) if spec['due_days'] is not None else None
            board = boards[position % len(boards)] if position >= len(BASE_TASKS) else Task.BoardType.STANDARD
            task = Task.objects.create(
                title=spec['title'],
                description=spec['description'],
                status=spec['status'],
                priority=spec['priority'],
                board_type=board,
                assignee=admin,
                due_date=due,
                position=position,
            )
            created += 1

            # ~40% of tasks get a future alert.
            if due and rng.random() < 0.4:
                TaskAlert.objects.create(
                    task=task,
                    notify_at=max(today, due - timedelta(days=1)),
                    note='Recordatorio: revisar avance antes del vencimiento.',
                )
            # ~50% of tasks get 1–2 comments.
            if admin and rng.random() < 0.5:
                for _ in range(rng.randint(1, 2)):
                    TaskComment.objects.create(
                        task=task, author=admin, text=rng.choice(COMMENTS),
                    )

        self.stdout.write(self.style.SUCCESS(
            f'{created} fake tasks created (with alerts and comments).'))
