"""Create the representative client/project distribution used by fake data."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Project, UserProfile
from content.fake_data import (
    DEFAULT_COUNT,
    add_seed_arguments,
    ensure_fake_data_allowed,
    seed_context,
)


User = get_user_model()
FAKE_EMAIL_DOMAIN = 'fake.projectapp.test'
FIRST_NAMES = (
    'Ana', 'Bruno', 'Camila', 'Diego', 'Elena', 'Felipe', 'Gabriela',
    'Hugo', 'Inés', 'Julián', 'Karen', 'Luis', 'Mariana', 'Nicolás',
)
LAST_NAMES = (
    'Álvarez', 'Benítez', 'Cárdenas', 'Domínguez', 'Escobar', 'Franco',
    'Gómez', 'Herrera', 'Ibarra', 'Jiménez', 'Londoño', 'Méndez',
)
PROJECT_LABELS = (
    'Portal comercial', 'Aplicación operativa', 'Sitio institucional',
    'Automatización interna', 'Plataforma de clientes', 'Tienda digital',
)
PROJECT_LIFECYCLE_STATUSES = (
    Project.STATUS_DEVELOPMENT,
    Project.STATUS_ACTIVE,
    Project.STATUS_PAUSED,
    Project.STATUS_SUSPENDED,
    Project.STATUS_COMPLETED,
    Project.STATUS_DECOMMISSIONED,
)


class Command(BaseCommand):
    help = (
        'Ensure a representative client/project graph: clients with no project, '
        'one project, several projects, and one high-volume client.'
    )

    def add_arguments(self, parser):
        add_seed_arguments(parser, count_default=DEFAULT_COUNT)

    def handle(self, *args, **options):
        ensure_fake_data_allowed('create_fake_clients_projects')
        context = seed_context(options, 'clients-projects')
        target = max(1, options['count'])
        admin = User.objects.filter(is_staff=True).order_by('pk').first()

        existing = list(UserProfile.objects.clients().order_by('pk'))
        missing = max(0, target - len(existing))
        initial_count = len(existing)
        for offset in range(missing):
            index = initial_count + offset
            email = f'client-{index + 1:03d}@{FAKE_EMAIL_DOMAIN}'
            first_name = FIRST_NAMES[index % len(FIRST_NAMES)]
            last_name = LAST_NAMES[index % len(LAST_NAMES)]
            user, _ = User.objects.update_or_create(
                username=email,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': index % 13 != 0,
                },
            )
            user.set_unusable_password()
            user.save(update_fields=['password'])
            company = f'Cliente Demo {index + 1:03d} S.A.S.'
            if offset == 0:
                company = 'ClienteExtremo' + ('SinEspacios' * 14)
                company = company[:200]
            profile, _ = UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'role': UserProfile.ROLE_CLIENT,
                    'is_onboarded': index % 5 != 0,
                    'email_verified': index % 3 != 0,
                    'profile_completed': index % 4 != 0,
                    'company_name': company,
                    'phone': f'+57310{index:07d}'[-13:],
                    'cedula': f'10{index:08d}',
                    'nit': f'901{index:06d}-{index % 10}' if index % 2 == 0 else '',
                    'created_by': admin,
                    'deactivated_at': (
                        context.anchor_now - timedelta(days=30 + index)
                        if index % 11 == 0 else None
                    ),
                },
            )
            existing.append(profile)

        profiles = list(UserProfile.objects.clients().order_by('pk')[:target])
        project_targets = self._project_targets(len(profiles))
        created_projects = 0
        for client_index, (profile, project_target) in enumerate(
            zip(profiles, project_targets, strict=True),
        ):
            current = list(Project.objects.filter(client=profile.user).order_by('pk'))
            first_new_project = len(current)
            for project_index in range(len(current), project_target):
                name = (
                    'Proyecto' + ('ExtremadamenteLargoSinEspacios' * 8)
                    if client_index == 0 and project_index == first_new_project
                    else (
                        f'{PROJECT_LABELS[project_index % len(PROJECT_LABELS)]} '
                        f'{client_index + 1:02d}-{project_index + 1:02d}'
                    )
                )[:200]
                date_bucket = project_index % 5
                start_date = context.anchor_date + timedelta(
                    days=(-240, -60, -7, 15, 120)[date_bucket],
                )
                end_date = start_date + timedelta(days=(30, 90, 180)[project_index % 3])
                Project.objects.create(
                    client=profile.user,
                    name=name,
                    description=(
                        'Proyecto de volumen representativo para probar listados, '
                        'filtros, totales y relaciones entre módulos.'
                    ),
                    status=(
                        PROJECT_LIFECYCLE_STATUSES[
                            project_index % len(PROJECT_LIFECYCLE_STATUSES)
                        ]
                    ),
                    progress=(project_index * 17) % 101,
                    start_date=start_date,
                    estimated_end_date=end_date,
                    production_url=f'https://project-{client_index + 1}-{project_index + 1}.example.test',
                )
                created_projects += 1

        total_projects = Project.objects.filter(
            client__profile__in=profiles,
        ).count()
        self.stdout.write(self.style.SUCCESS(
            f'Representative graph ready: {len(profiles)} clients, '
            f'{total_projects} projects ({created_projects} new).',
        ))

    @staticmethod
    def _project_targets(count):
        """Default 60-client profile => 20 + (9×3) + (20×1) + (30×0)."""

        if count <= 0:
            return []
        zero_count = count // 2
        multi_count = min(max(1, round(count * 0.15)), max(0, count - 1))
        single_count = max(0, count - 1 - multi_count - zero_count)
        targets = [20]
        targets.extend([3] * multi_count)
        targets.extend([1] * single_count)
        targets.extend([0] * zero_count)
        return targets[:count] + [0] * max(0, count - len(targets))
