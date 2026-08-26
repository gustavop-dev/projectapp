"""Create a coherent, skewed client-communications history for development."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import UserProfile
from content.fake_data import add_seed_arguments, ensure_fake_data_allowed, seed_context
from content.models import CommunicationMessage, CommunicationThread, Document
from content.services import communication_service


THREAD_TOPICS = (
    'Aprobación de alcance', 'Coordinación de entrega', 'Seguimiento de pago',
    'Acceso al ambiente de pruebas', 'Comentarios sobre el diseño',
)


class Command(BaseCommand):
    help = (
        'Create representative communication threads: single-message, regular '
        'and long histories with replies, failures, voids and date corrections.'
    )

    def add_arguments(self, parser):
        add_seed_arguments(parser, count_default=60)

    def handle(self, *args, **options):
        ensure_fake_data_allowed('create_fake_communications')
        context = seed_context(options, 'communications')
        requested = max(1, options['count'])

        if CommunicationThread.objects.filter(title__startswith='[Demo]').exists():
            self.stdout.write(self.style.WARNING(
                'Demo communications already exist — skipped. Use '
                'create_fake_data --replace to regenerate deterministically.',
            ))
            return

        clients = list(
            UserProfile.objects.clients()
            .prefetch_related('user__projects')
            .order_by('id')
        )
        if not clients:
            self.stdout.write(self.style.WARNING(
                'No clients found. Run create_fake_clients_projects first.',
            ))
            return

        admin = get_user_model().objects.filter(is_staff=True).order_by('id').first()
        single_cut = max(1, round(requested * 0.20))
        long_cut = requested - max(1, round(requested * 0.20))
        message_total = 0

        for index in range(requested):
            # Concentrate one third of the threads on the first client; the
            # remainder rotates across the catalog, leaving clients with 0/1/N.
            if index < requested // 3 or len(clients) == 1:
                client = clients[0]
            else:
                client = clients[
                    1 + ((index - requested // 3) % (len(clients) - 1))
                ]
            projects = list(client.user.projects.all())
            project = projects[index % len(projects)] if projects and index % 3 else None
            title = f'[Demo] {THREAD_TOPICS[index % len(THREAD_TOPICS)]} #{index + 1}'
            if index == requested - 1:
                title = ('[Demo] ' + ('HiloExtremoSinEspacios' * 12))[:255]
            thread = communication_service.create_thread(
                actor=admin, client=client, project=project, title=title,
            )

            # Preserve the historical one-thread smoke fixture while the
            # representative default still includes genuine one-message rows.
            if requested == 1:
                target_messages = 3
            elif index < single_cut:
                target_messages = 1
            elif index >= long_cut:
                target_messages = 12
            else:
                target_messages = 3

            base_at = context.anchor_now - timedelta(
                days=360 - ((index * 360) // max(1, requested - 1)),
            )
            created_messages = []
            documents = list(
                Document.objects.filter(client_user=client.user).order_by('id')[:3]
            )

            for message_index in range(target_messages):
                incoming = message_index % 2 == 1
                channel = (
                    CommunicationMessage.Channel.EMAIL
                    if (index + message_index) % 2 == 0
                    else CommunicationMessage.Channel.WHATSAPP
                )
                direction = (
                    CommunicationMessage.Direction.INCOMING if incoming
                    else CommunicationMessage.Direction.OUTGOING
                )
                if requested == 1:
                    status = (
                        CommunicationMessage.Status.SENT,
                        CommunicationMessage.Status.RECEIVED,
                        CommunicationMessage.Status.DRAFT,
                    )[message_index]
                elif incoming:
                    status = CommunicationMessage.Status.RECEIVED
                elif message_index == target_messages - 1 and index % 6 == 0:
                    status = CommunicationMessage.Status.DRAFT
                elif (index + message_index) % 9 == 0:
                    status = CommunicationMessage.Status.FAILED
                else:
                    status = CommunicationMessage.Status.SENT

                occurred_at = base_at + timedelta(hours=message_index * 4)
                if status == CommunicationMessage.Status.DRAFT and index % 2 == 0:
                    occurred_at = context.anchor_now + timedelta(days=7 + index % 30)
                reply_to = None
                if created_messages:
                    candidate = created_messages[-1]
                    if (
                        candidate.direction != direction
                        and candidate.status != CommunicationMessage.Status.DRAFT
                        and not candidate.voided_at
                    ):
                        reply_to = candidate

                subject = (
                    f'{THREAD_TOPICS[index % len(THREAD_TOPICS)]} '
                    f'— actualización {message_index + 1}'
                    if channel == CommunicationMessage.Channel.EMAIL else ''
                )
                content = (
                    'Mensaje representativo con contexto suficiente para probar '
                    'la lectura cronológica, respuestas y estados operativos.'
                )
                if target_messages == 12 and message_index == 5:
                    content = ('ContenidoExtensoSinEspacios' * 80)[:1800]
                attachment_ids = []
                if documents and message_index in (0, 5):
                    attachment_ids = [
                        document.pk
                        for document in documents[:1 + (index % min(2, len(documents)))]
                    ]
                message = communication_service.create_message(
                    thread=thread,
                    actor=admin,
                    channel=channel,
                    direction=direction,
                    status=status,
                    subject=subject,
                    content=content,
                    occurred_at=occurred_at,
                    reply_to=reply_to,
                    document_ids=attachment_ids,
                )
                created_messages.append(message)
                message_total += 1

            immutable = [
                message for message in created_messages
                if message.status != CommunicationMessage.Status.DRAFT
            ]
            if immutable and index % 10 == 2:
                message = immutable[0]
                communication_service.correct_message_date(
                    message,
                    actor=admin,
                    occurred_at=message.occurred_at + timedelta(hours=1),
                    reason='Corrección intencional del fixture representativo.',
                )
            if immutable and index % 10 == 3:
                communication_service.void_message(
                    immutable[-1],
                    actor=admin,
                    reason='Anulación intencional para cubrir el historial.',
                )
            if index % 4 == 3:
                communication_service.close_thread(thread, actor=admin)
                CommunicationThread.objects.filter(pk=thread.pk).update(
                    closed_at=context.anchor_now - timedelta(days=index % 30),
                )

        self.stdout.write(self.style.SUCCESS(
            f'Created {requested} demo threads and {message_total} messages '
            f'(seed={context.seed}, anchor={context.anchor_date}).',
        ))
