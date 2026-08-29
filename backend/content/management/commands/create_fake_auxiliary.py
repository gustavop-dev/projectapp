"""Seed smaller visible modules omitted by the historical orchestrator."""

from datetime import timedelta

from django.core.management.base import BaseCommand

from accounts.models import UserProfile
from content.fake_data import add_seed_arguments, ensure_fake_data_allowed, seed_context
from content.models import (
    AdditionalModule,
    AdditionalModuleShareLink,
    AdditionalModuleShareView,
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
    help = (
        'Create representative Email, QR, Linktree, LinkedIn, additional-module '
        'sharing and MCP history.'
    )

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

        modules = list(
            AdditionalModule.objects.filter(
                is_active=True,
                category__is_active=True,
            ).order_by('category__order', 'order', 'pk')
        )
        share_target = 0
        if modules:
            AdditionalModuleShareLink.objects.filter(
                recipient_label__startswith='[Demo] Catálogo',
            ).delete()
            share_specs = (
                ('Selección breve', 'es', 3, 0, True),
                ('Selección consultada', 'es', 6, 1, True),
                ('Catálogo completo', 'es', len(modules), 2, True),
                ('Selection in English', 'en', 4, 1, True),
                ('Enlace retirado', 'es', 3, 0, False),
            )
            for index, (label, language, module_count, view_count, is_active) in enumerate(share_specs):
                link = AdditionalModuleShareLink.objects.create(
                    uuid=context.uuid(f'additional-modules-share-{index}'),
                    recipient_label=f'[Demo] Catálogo — {label}',
                    client=clients[index % len(clients)] if clients else None,
                    language=language,
                    is_active=is_active,
                    revoked_at=(
                        context.anchor_now - timedelta(days=2)
                        if not is_active else None
                    ),
                )
                selected = modules if module_count >= len(modules) else modules[:module_count]
                link.selected_modules.set(selected)

                viewed_at_values = []
                for view_index in range(view_count):
                    event = AdditionalModuleShareView.objects.create(
                        share_link=link,
                        session_id=f'demo-session-{index}-{view_index}',
                        ip_address='192.0.2.10',
                        user_agent='ProjectApp representative dataset',
                    )
                    viewed_at = context.anchor_now - timedelta(
                        days=5 - index,
                        hours=view_index,
                    )
                    AdditionalModuleShareView.objects.filter(pk=event.pk).update(
                        viewed_at=viewed_at,
                    )
                    viewed_at_values.append(viewed_at)

                if viewed_at_values:
                    AdditionalModuleShareLink.objects.filter(pk=link.pk).update(
                        view_count=len(viewed_at_values),
                        first_viewed_at=min(viewed_at_values),
                        last_viewed_at=max(viewed_at_values),
                    )
                share_target += 1

        ViewMapSettings.load()

        self.stdout.write(self.style.SUCCESS(
            f'Auxiliary modules ready: {linktree_target} linktrees, {qr_target} QR '
            f'cards, {linkedin_target} LinkedIn posts, {share_target} catalog '
            f'shares, {count} email/MCP rows.',
        ))
