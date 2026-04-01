from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = (
        'Create all fake data (contacts, proposals, blog posts). '
        'Business proposals include all default sections plus a populated technical_document '
        '(modo técnico / panel Doc. técnico). '
        'Recommended order for a full local demo: (1) create_fake_data, (2) seed_platform_data — '
        'or pass --with-platform to run seed_platform_data after this command.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', type=int, default=10,
            help='Number of records to create per entity (default: 10)',
        )
        parser.add_argument(
            '--with-platform',
            action='store_true',
            help='After content fake data, run accounts.seed_platform_data (JWT demo: projects, Kanban, payments).',
        )

    def handle(self, *args, **options):
        number_of_records = options['count']

        # Create admin superuser if not already present
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
            self.stdout.write(self.style.SUCCESS('Admin superuser created (username: admin / password: admin)'))
        else:
            self.stdout.write(self.style.WARNING('Admin superuser already exists — skipped'))

        # Create fake data for contacts
        self.stdout.write(self.style.SUCCESS('Creating fake contacts...'))
        call_command('create_contacts', number_of_records)

        # Create fake data for business proposals
        self.stdout.write(self.style.SUCCESS('Creating fake business proposals...'))
        call_command('create_fake_proposals', '--count', str(number_of_records))

        # Create fake data for blog posts
        self.stdout.write(self.style.SUCCESS('Creating fake blog posts...'))
        call_command('create_fake_blog_posts', '--count', str(number_of_records))

        self.stdout.write(self.style.SUCCESS('All fake data has been created'))

        if options.get('with_platform'):
            self.stdout.write(self.style.SUCCESS('Running seed_platform_data (platform graph)...'))
            call_command('seed_platform_data')
            self.stdout.write(self.style.SUCCESS('Platform seed finished.'))
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Tip: run `python manage.py seed_platform_data` for platform/JWT demo data '
                    '(projects, deliverables, requirements, payments), or re-run with --with-platform.'
                )
            )
