"""Create a coherent client-communications history for local/demo use."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import UserProfile
from content.models import CommunicationMessage, CommunicationThread, Document
from content.services import communication_service


THREAD_TOPICS = (
    'Aprobación de alcance',
    'Coordinación de entrega',
    'Seguimiento de pago',
    'Acceso al ambiente de pruebas',
    'Comentarios sobre el diseño',
)


class Command(BaseCommand):
    help = 'Create demo communication threads with messages and referenced documents.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=20)

    def handle(self, *args, **options):
        if CommunicationThread.objects.filter(title__startswith='[Demo]').exists():
            self.stdout.write(self.style.WARNING(
                'Demo communications already exist — skipped.',
            ))
            return

        clients = list(
            UserProfile.objects.clients()
            .prefetch_related('user__projects')
            .order_by('id')
        )
        if not clients:
            self.stdout.write(self.style.WARNING(
                'No clients found. Run seed_platform_data first.',
            ))
            return

        admin = get_user_model().objects.filter(is_staff=True).order_by('id').first()
        now = timezone.now()
        requested = max(1, options['count'])

        for index in range(requested):
            client = clients[index % len(clients)]
            projects = list(client.user.projects.all())
            project = projects[index % len(projects)] if projects and index % 3 else None
            thread = communication_service.create_thread(
                actor=admin,
                client=client,
                project=project,
                title=f'[Demo] {THREAD_TOPICS[index % len(THREAD_TOPICS)]} #{index + 1}',
            )
            first_at = now - timedelta(days=requested - index, hours=2)
            documents = list(
                Document.objects.filter(client_user=client.user).order_by('id')[:1]
            )
            outgoing = communication_service.create_message(
                thread=thread,
                actor=admin,
                channel=CommunicationMessage.Channel.EMAIL,
                direction=CommunicationMessage.Direction.OUTGOING,
                status=CommunicationMessage.Status.SENT,
                subject=f'Seguimiento: {THREAD_TOPICS[index % len(THREAD_TOPICS)]}',
                content='Te comparto el avance y quedo atento a tus comentarios.',
                occurred_at=first_at,
                document_ids=[document.id for document in documents],
            )
            communication_service.create_message(
                thread=thread,
                actor=admin,
                channel=CommunicationMessage.Channel.WHATSAPP,
                direction=CommunicationMessage.Direction.INCOMING,
                status=CommunicationMessage.Status.RECEIVED,
                subject='',
                content='Recibido, gracias. Lo reviso y te confirmo.',
                occurred_at=first_at + timedelta(hours=3),
                reply_to=outgoing,
            )
            if index % 2 == 0:
                communication_service.create_message(
                    thread=thread,
                    actor=admin,
                    channel=CommunicationMessage.Channel.WHATSAPP,
                    direction=CommunicationMessage.Direction.OUTGOING,
                    status=CommunicationMessage.Status.DRAFT,
                    subject='',
                    content='Perfecto. Mañana te envío la siguiente actualización.',
                    occurred_at=first_at + timedelta(hours=4),
                )
            if index % 4 == 3:
                communication_service.close_thread(thread, actor=admin)

        self.stdout.write(self.style.SUCCESS(
            f'Created {requested} demo communication thread(s).',
        ))
