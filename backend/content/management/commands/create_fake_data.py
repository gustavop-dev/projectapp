import traceback

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = (
        'Create fake data across ALL features so the dev environment is playable: '
        'contacts, business proposals (with all sections + technical_document), blog posts, '
        'portfolio works, Kanban tasks, web-app diagnostics, the platform graph '
        '(projects, requirements, deliverables, change requests, bugs, hosting/payments, '
        'notifications) and the commercial documents graph (issuer, folders, tags, '
        'markdown docs + collection accounts). '
        'Use --count to control volume (default 40) and --skip-* to omit a feature.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', type=int, default=40,
            help='Number of records to create per entity (default: 40).',
        )
        # Optional positional for compatibility with the fake-data-refresh skill,
        # which invokes `manage.py create_fake_data <N>`.
        parser.add_argument(
            'count_pos', nargs='?', type=int, default=None,
            help='Positional alias for --count (used by the fake-data-refresh skill).',
        )
        parser.add_argument('--skip-contacts', action='store_true')
        parser.add_argument('--skip-proposals', action='store_true')
        parser.add_argument('--skip-blog', action='store_true')
        parser.add_argument('--skip-portfolio', action='store_true')
        parser.add_argument('--skip-tasks', action='store_true')
        parser.add_argument('--skip-diagnostics', action='store_true')
        parser.add_argument('--skip-platform', action='store_true')
        parser.add_argument('--skip-documents', action='store_true')
        parser.add_argument('--skip-accounting', action='store_true')

    def handle(self, *args, **options):
        count = options['count_pos'] if options['count_pos'] is not None else options['count']
        n = str(count)

        # Admin superuser (kept for legacy quick-login: admin / admin).
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@admin.com',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            admin.set_password('admin')
            admin.save()
            self.stdout.write(self.style.SUCCESS(
                'Admin superuser created (username: admin / password: admin)'))
        else:
            self.stdout.write(self.style.WARNING('Admin superuser already exists — skipped'))

        # Each feature is run in isolation: one failing seeder must not abort the
        # whole run, so the dev DB still ends up populated for every other feature.
        self._ok = []
        self._failed = []

        if not options['skip_contacts']:
            self._run('contacts', 'create_contacts', n)
        if not options['skip_proposals']:
            # Hour packages must exist before proposals so the
            # commercial_conditions sections seed from the catalog.
            self._run('hour-packages', 'create_fake_hour_packages')
            self._run('proposals', 'create_fake_proposals', '--count', n)
        if not options['skip_blog']:
            self._run('blog', 'create_fake_blog_posts', '--count', n)
        if not options['skip_portfolio']:
            self._run('portfolio', 'create_fake_portfolio', '--count', n)
        if not options['skip_tasks']:
            self._run('tasks', 'create_fake_tasks', '--count', n)
        if not options['skip_diagnostics']:
            self._run(
                'diagnostics', 'create_fake_diagnostics', '--count', n,
                '--with-pricing', '--with-states', '--with-views',
            )

        # Platform graph must run before documents: collection accounts need clients/projects.
        if not options['skip_platform']:
            self._run('platform', 'seed_platform_data')
            self._run('demo-clients', 'seed_demo_clients')
            self._run('platform-enrich', 'enrich_platform_data')

        # Saved filter tabs for staff (otherwise they only lazy-seed on first GET).
        self._run('filter-tabs', 'seed_filter_tabs')

        if not options['skip_documents']:
            self._run('documents', 'create_fake_documents', '--count', n)

        if not options.get('skip_accounting'):
            self._run('accounting', 'create_fake_accounting', '--count', n)

        # Summary.
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Done. Populated: {", ".join(self._ok) or "none"}'))
        if self._failed:
            self.stdout.write(self.style.ERROR(
                f'Failed features: {", ".join(self._failed)} '
                '(see traceback above; other features were still populated).'))

    def _run(self, label, command, *args):
        self.stdout.write(self.style.SUCCESS(f'→ {label} ({command})...'))
        try:
            call_command(command, *args)
            self._ok.append(label)
        except Exception:  # noqa: BLE001 — keep going so other features still seed
            self._failed.append(label)
            self.stdout.write(self.style.ERROR(f'✗ {label} failed:'))
            self.stdout.write(traceback.format_exc())
