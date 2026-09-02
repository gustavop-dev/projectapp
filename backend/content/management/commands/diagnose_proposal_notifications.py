"""
Diagnose the "client opened the proposal" notification pipeline.

The sales team reported not receiving first-view / stakeholder notifications.
Those emails are queued as Huey tasks (async in production) and sent over
SMTP, so a silent failure can live in several places: the Huey worker not
running, SMTP credentials, a disabled email template, or empty recipients.

This command inspects each link of the chain and (optionally) sends a real
test email so the exact failing step is identified end to end.

Usage:
    python manage.py diagnose_proposal_notifications
    python manage.py diagnose_proposal_notifications --send --to you@example.com
    python manage.py diagnose_proposal_notifications --proposal-id 123 --send
"""

import os
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from django.utils import timezone

from content.models import BusinessProposal
from content.services.email_delivery_service import (
    DeliveryClassification,
    EmailDeliveryGateway,
    EmailMultiAlternatives,
)
from content.services.proposal_email_service import ProposalEmailService


class Command(BaseCommand):
    help = (
        'Diagnose the proposal open-notification pipeline '
        '(Huey, SMTP, templates, recipients) and optionally send a test email.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--send',
            action='store_true',
            help='Actually attempt to send a test email over SMTP.',
        )
        parser.add_argument(
            '--to',
            type=str,
            default=None,
            help='Override recipient for the SMTP test (defaults to the '
                 'configured notification recipients).',
        )
        parser.add_argument(
            '--proposal-id',
            type=int,
            default=None,
            help='Also exercise the real first-view notification template '
                 'path for this proposal id.',
        )
        parser.add_argument(
            '--allow-non-production',
            action='store_true',
            help='Run diagnostics against non-production settings explicitly.',
        )

    # -- helpers ---------------------------------------------------------

    def _ok(self, msg):
        self.stdout.write(self.style.SUCCESS(f'  ✓ {msg}'))

    def _warn(self, msg):
        self.stdout.write(self.style.WARNING(f'  ⚠ {msg}'))

    def _err(self, msg):
        self.stdout.write(self.style.ERROR(f'  ✗ {msg}'))

    def _section(self, title):
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING(title))

    # -- handle ----------------------------------------------------------

    def handle(self, *args, **options):
        settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', '')
        if (
            not settings_module.endswith('settings_prod')
            and not options['allow_non_production']
        ):
            raise CommandError(
                'Refusing to diagnose with non-production settings '
                f'({settings_module or "unset"}). Set '
                'DJANGO_SETTINGS_MODULE=projectapp.settings_prod or pass '
                '--allow-non-production intentionally.'
            )
        self.stdout.write(
            self.style.HTTP_INFO('Proposal notification pipeline diagnosis')
        )

        self._check_huey()
        self._check_email_settings()
        recipients = self._check_recipients()
        self._check_templates()
        self._check_delivery_state()

        if options['proposal_id']:
            self._check_template_render(options['proposal_id'])

        if options['send']:
            self._send_test_email(options['to'], recipients)
        else:
            self._section('5. SMTP delivery')
            self.stdout.write(
                '  (skipped — pass --send to attempt a real test email)'
            )

        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Diagnosis complete.'))

    # -- checks ----------------------------------------------------------

    def _check_huey(self):
        self._section('1. Huey async queue')
        huey = getattr(settings, 'HUEY', None)
        if huey is None:
            self._err('settings.HUEY is not configured.')
            return
        immediate = getattr(huey, 'immediate', None)
        if immediate:
            self._ok('immediate=True — tasks run synchronously (dev/staging). '
                     'No worker required.')
        else:
            self._warn('immediate=False — a Huey worker must be running '
                       '(projectapp-huey.service). If it is down, '
                       'notifications never execute.')
            try:
                pending = huey.pending_count()
                if pending:
                    self._warn(f'{pending} task(s) pending in the queue — '
                               'consistent with a stopped/slow worker.')
                else:
                    self._ok('0 tasks pending in the queue.')
            except Exception as exc:  # pragma: no cover - storage backend dependent
                self._warn(f'Could not read pending task count: {exc}')

    def _check_email_settings(self):
        self._section('2. Email backend / SMTP settings')
        mailer = settings.MAILERS.get('default', {})
        backend = mailer.get('BACKEND', '')
        options = mailer.get('OPTIONS', {})
        self.stdout.write(f'  MAILERS["default"]["BACKEND"] = {backend}')
        if 'console' in backend or 'locmem' in backend or 'dummy' in backend:
            self._warn('Non-SMTP backend — emails are not actually delivered.')
        else:
            self._ok('SMTP backend configured.')
        self.stdout.write(
            f'  SMTP = {options.get("host", "")}:'
            f'{options.get("port", "")} '
            f'(SSL={options.get("use_ssl", False)}, '
            f'TLS={options.get("use_tls", False)})'
        )
        user = options.get('username', '')
        pwd = options.get('password', '')
        if user:
            self._ok(f'SMTP username set ({user}).')
        else:
            self._err('SMTP username is empty.')
        if pwd:
            self._ok('SMTP password set.')
        else:
            self._err('SMTP password is empty.')
        self.stdout.write(
            f'  DEFAULT_FROM_EMAIL = {getattr(settings, "DEFAULT_FROM_EMAIL", "")}'
        )

    def _check_recipients(self):
        self._section('3. Notification recipients')
        recipients = ProposalEmailService._get_notification_recipients()
        if recipients:
            self._ok(f'Recipients: {", ".join(recipients)}')
        else:
            self._err('No notification recipients resolved.')
        return recipients

    def _check_templates(self):
        self._section('4. Email templates active')
        for key in ('proposal_first_view_notification',
                    'proposal_stakeholder_detected'):
            try:
                active = ProposalEmailService._is_template_active(key)
            except Exception as exc:
                self._err(f'{key}: error checking — {exc}')
                continue
            if active:
                self._ok(f'{key}: active')
            else:
                self._warn(f'{key}: DISABLED — notifications of this type are '
                           'skipped before any send is attempted.')

    def _check_delivery_state(self):
        self._section('4b. Durable first-view delivery state')
        try:
            rows = {
                row['first_view_notification_status']: row['count']
                for row in (
                    BusinessProposal.objects
                    .values('first_view_notification_status')
                    .annotate(count=Count('id'))
                )
            }
            stale = BusinessProposal.objects.filter(
                first_view_notification_status='sending',
                first_view_notification_attempted_at__lt=(
                    timezone.now() - timedelta(minutes=10)
                ),
            ).count()
        except Exception as exc:
            self._err(f'Could not query durable delivery state: {exc}')
            return
        for status_name in (
            'pending', 'sending', 'failed', 'sent', 'skipped',
            'legacy_unverified', 'not_started',
        ):
            self.stdout.write(f'  {status_name}: {rows.get(status_name, 0)}')
        if stale:
            self._warn(f'{stale} delivery claim(s) stale for more than 10 minutes.')
        elif rows.get('pending', 0) or rows.get('failed', 0):
            self._warn('Pending or failed deliveries require reconciliation.')
        else:
            self._ok('No pending, failed, or stale delivery state detected.')

    def _check_template_render(self, proposal_id):
        self._section(f'4c. Render first-view template for proposal {proposal_id}')
        try:
            proposal = BusinessProposal.objects.get(pk=proposal_id)
        except BusinessProposal.DoesNotExist:
            self._err(f'Proposal {proposal_id} not found.')
            return
        try:
            sent = ProposalEmailService.send_first_view_notification(proposal)
            if sent:
                self._ok('send_first_view_notification returned True '
                         '(rendered + sent).')
            else:
                self._warn('send_first_view_notification returned False '
                           '(template disabled, status suppressed, or send '
                           'failed — see logs above).')
        except Exception as exc:
            self._err(f'Exception while rendering/sending: {exc!r}')

    def _send_test_email(self, to_override, recipients):
        self._section('5. SMTP delivery (live test)')
        to = [to_override] if to_override else recipients
        if not to:
            self._err('No recipient available for the test send.')
            return
        try:
            msg = EmailMultiAlternatives(
                subject='[diagnose] Proposal notifications SMTP test',
                body='This is a connectivity test from '
                     'diagnose_proposal_notifications.',
                from_email=ProposalEmailService._get_from_email(),
                to=to,
            )
            EmailDeliveryGateway.send(
                msg,
                template_key='proposal_notification_diagnostic',
                classification=DeliveryClassification.INTERNAL,
            )
            self._ok(f'Test email sent to {", ".join(to)} without raising.')
        except Exception as exc:
            self._err(f'SMTP send failed: {exc!r}')
