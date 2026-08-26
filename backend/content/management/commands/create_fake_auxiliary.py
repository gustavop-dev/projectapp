"""Seed smaller visible modules omitted by the historical orchestrator."""

from datetime import timedelta

from django.core.management.base import BaseCommand

from accounts.models import UserProfile
from content.fake_data import add_seed_arguments, ensure_fake_data_allowed, seed_context
from content.models import (
    EmailCopyRecipient,
    EmailLog,
    LinkedInPost,
    Linktree,
    LinktreeButton,
    McpConnector,
    McpRequestLog,
    QRCard,
    ViewMapSettings,
)


class Command(BaseCommand):
    help = 'Create representative Email, QR, Linktree, LinkedIn and MCP history.'

    def add_arguments(self, parser):
        add_seed_arguments(parser, count_default=60)

    def handle(self, *args, **options):
        ensure_fake_data_allowed('create_fake_auxiliary')
        context = seed_context(options, 'auxiliary')
        count = max(1, options['count'])
        clients = list(UserProfile.objects.clients().order_by('pk'))

        linktree_target = max(1, round(count * 0.20))
        linktrees = []
        for index in range(linktree_target):
            linktree, _ = Linktree.objects.update_or_create(
                id=context.uuid(f'linktree-{index}'),
                defaults={
                    'handle': f'demo-{index + 1:02d}',
                    'name': f'Linktree demo {index + 1:02d}',
                    'kind': (
                        Linktree.Kind.PERSONAL if index % 2 == 0
                        else Linktree.Kind.COMPANY
                    ),
                    'display_name': f'Perfil representativo {index + 1}',
                    'role': 'Cliente ProjectApp',
                    'bio': 'Perfil con enlaces variados para validar el módulo.',
                    'vcard_email': f'linktree-{index + 1}@example.test',
                    'vcard_url': f'https://example.test/linktree-{index + 1}',
                    'is_active': index % 5 != 0,
                },
            )
            linktrees.append(linktree)
            button_specs = (
                (LinktreeButton.Tier.PRIMARY, LinktreeButton.Action.WEB, 'Sitio web'),
                (LinktreeButton.Tier.FEATURED, LinktreeButton.Action.WHATSAPP, 'WhatsApp'),
                (LinktreeButton.Tier.PAIR, LinktreeButton.Action.LINKEDIN, 'LinkedIn'),
                (LinktreeButton.Tier.PAIR, LinktreeButton.Action.EMAIL, 'Correo'),
            )
            for order, (tier, action, label) in enumerate(button_specs):
                LinktreeButton.objects.update_or_create(
                    linktree=linktree,
                    order=order,
                    defaults={
                        'tier': tier,
                        'action': action,
                        'label': label,
                        'href': (
                            '' if order == 3 and index % 3 == 0
                            else f'https://example.test/{linktree.handle}/{order}'
                        ),
                        'is_active': True,
                    },
                )

        qr_target = max(1, round(count * 0.50))
        for index in range(qr_target):
            uses_linktree = bool(linktrees) and index % 2 == 1
            QRCard.objects.update_or_create(
                id=context.uuid(f'qr-{index}'),
                defaults={
                    'name': (
                        ('TarjetaQRExtremaSinEspacios' * 12)[:255]
                        if index == qr_target - 1
                        else f'Tarjeta QR demo {index + 1:02d}'
                    ),
                    'destination_type': (
                        QRCard.DestinationType.LINKTREE if uses_linktree
                        else QRCard.DestinationType.URL
                    ),
                    'linktree': linktrees[index % len(linktrees)] if uses_linktree else None,
                    'destination_url': (
                        '' if uses_linktree else f'https://example.test/qr/{index + 1}'
                    ),
                    'is_active': index % 7 != 0,
                },
            )

        linkedin_target = max(1, round(count / 3))
        statuses = (
            LinkedInPost.STATUS_DRAFT,
            LinkedInPost.STATUS_SCHEDULED,
            LinkedInPost.STATUS_PUBLISHED,
            LinkedInPost.STATUS_FAILED,
        )
        for index in range(linkedin_target):
            status = statuses[index % len(statuses)]
            LinkedInPost.objects.create(
                commentary=(
                    f'[Demo] Publicación representativa {index + 1}. '
                    'Contenido preparado para revisar estados y fechas.'
                ),
                status=status,
                scheduled_at=(
                    context.anchor_now + timedelta(days=7 + index)
                    if status == LinkedInPost.STATUS_SCHEDULED else None
                ),
                published_at=(
                    context.anchor_now - timedelta(days=index + 1)
                    if status == LinkedInPost.STATUS_PUBLISHED else None
                ),
                linkedin_post_id=(
                    f'urn:li:share:demo-{index + 1}'
                    if status == LinkedInPost.STATUS_PUBLISHED else ''
                ),
                error_message=(
                    'Error simulado de proveedor.'
                    if status == LinkedInPost.STATUS_FAILED else ''
                ),
            )

        for index in range(max(0, count - EmailLog.objects.count())):
            client = clients[index % len(clients)] if clients else None
            status = list(EmailLog.Status.values)[index % len(EmailLog.Status.values)]
            log = EmailLog.objects.create(
                template_key='standalone_composed',
                recipient=(
                    client.user.email if client else f'email-{index + 1}@example.test'
                ),
                subject=f'[Demo] Historial de correo {index + 1}',
                status=status,
                error_message='Rebote simulado.' if status == EmailLog.Status.FAILED else '',
                client=client,
                audience=EmailLog.Audience.CLIENT,
                delivery_id=context.uuid(f'email-delivery-{index}'),
                metadata={'fake_data': True, 'sequence': index + 1},
            )
            EmailLog.objects.filter(pk=log.pk).update(
                sent_at=context.anchor_now - timedelta(days=index % 120),
            )

        # Never attach simulated traffic to a configured real connector.
        connectors = list(
            McpConnector.objects.filter(slug__startswith='demo-').order_by('pk')
        )
        if not connectors:
            connectors = [
                McpConnector.objects.create(
                    slug=f'demo-{index + 1}',
                    name=f'Conector demo {index + 1}',
                    description='Conector inactivo sin credenciales reales.',
                    is_active=False,
                )
                for index in range(3)
            ]
        for index in range(count):
            event, label = McpRequestLog.EVENT_CHOICES[
                index % len(McpRequestLog.EVENT_CHOICES)
            ]
            row = McpRequestLog.objects.create(
                connector=connectors[index % len(connectors)],
                event=event,
                ok=event in ('handshake', 'tool_call'),
                detail=f'[Demo] {label} #{index + 1}',
            )
            McpRequestLog.objects.filter(pk=row.pk).update(
                created_at=context.anchor_now - timedelta(hours=index * 6),
            )

        EmailCopyRecipient.objects.update_or_create(
            email='copies-active@example.test',
            defaults={'is_active': True},
        )
        EmailCopyRecipient.objects.update_or_create(
            email='copies-paused@example.test',
            defaults={'is_active': False},
        )
        ViewMapSettings.load()

        self.stdout.write(self.style.SUCCESS(
            f'Auxiliary modules ready: {linktree_target} linktrees, {qr_target} QR '
            f'cards, {linkedin_target} LinkedIn posts, {count} email/MCP rows.',
        ))
