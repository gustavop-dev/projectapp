"""
Seed the code-level SavedFilterTab defaults for staff users.

Idempotent: without --force it only seeds (user, view) pairs that have zero
tabs; with --force it upserts the registry entries by name without deleting
any extra tabs the user created.

Usage:
  python manage.py seed_filter_tabs
  python manage.py seed_filter_tabs --user admin@example.com --view client
  python manage.py seed_filter_tabs --force
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.default_filter_tabs import DEFAULT_FILTER_TABS
from accounts.models import SavedFilterTab
from accounts.services import saved_filter_tab_service

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed default SavedFilterTab rows for staff users from the code registry.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            help='Email or username of a single user to seed (default: all staff).',
        )
        parser.add_argument(
            '--view',
            help='Single view to seed (default: every view in the registry).',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Upsert registry tabs by name even when the user already has tabs.',
        )

    def handle(self, *args, **options):
        if options['user']:
            user = (
                User.objects.filter(email__iexact=options['user']).first()
                or User.objects.filter(username__iexact=options['user']).first()
            )
            if user is None:
                raise CommandError(f'Usuario no encontrado: {options["user"]}')
            users = [user]
        else:
            users = list(User.objects.filter(is_staff=True))

        if options['view']:
            valid_views = {choice[0] for choice in SavedFilterTab.VIEW_CHOICES}
            if options['view'] not in valid_views:
                raise CommandError(
                    f'Vista no válida: {options["view"]}. Opciones: {sorted(valid_views)}'
                )
            views = [options['view']]
        else:
            views = list(DEFAULT_FILTER_TABS.keys())

        for user in users:
            for view in views:
                created, updated = saved_filter_tab_service.seed_default_tabs(
                    user, view, force=options['force'],
                )
                label = user.email or user.username
                if created or updated:
                    self.stdout.write(
                        f'{label} / {view}: created={created} updated={updated}'
                    )
                else:
                    self.stdout.write(f'{label} / {view}: skipped')
