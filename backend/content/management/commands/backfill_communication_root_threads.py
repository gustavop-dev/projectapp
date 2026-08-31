"""Provisiona la comunicación madre de los proyectos históricos.

El signal sólo corre al CREAR un proyecto, así que los que ya existían no la
tienen. Dry-run por defecto, como el resto de los backfills del repo: imprime el
plan con el motivo de cada salto y sólo escribe con `--apply`.

También adopta comunicaciones madre de cliente cuando el operador las nombra
explícitamente — nunca por inferencia, y nunca de forma automática: hay decenas
de perfiles de cliente y provisionarlos a todos llenaría el módulo de hilos
vacíos.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import Project, UserProfile
from content.models import CommunicationThread
from content.services.client_communication_service import adopt_client_thread
from content.services.project_communication_service import (
    ensure_project_thread, resolve_client_profile,
)


class Command(BaseCommand):
    help = (
        'Crea la comunicación madre de los proyectos que no la tienen y adopta '
        'las de cliente indicadas. Dry-run salvo que se pase --apply.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply', action='store_true',
            help='Escribe los cambios. Sin este flag sólo se imprime el plan.',
        )
        parser.add_argument(
            '--adopt-client-thread', action='append', default=[],
            metavar='THREAD_ID:PROFILE_ID',
            help='Hilo existente que pasa a ser la madre de ese cliente (repetible).',
        )

    def _parse_adoptions(self, values):
        pairs = {}
        for value in values:
            try:
                thread_raw, profile_raw = value.split(':', 1)
                thread_id, profile_id = int(thread_raw), int(profile_raw)
            except (AttributeError, TypeError, ValueError) as exc:
                raise CommandError(
                    '--adopt-client-thread usa el formato HILO:PERFIL.'
                ) from exc
            if thread_id <= 0 or profile_id <= 0:
                raise CommandError('--adopt-client-thread requiere ids positivos.')
            pairs[thread_id] = profile_id
        return pairs

    def handle(self, *args, **options):
        apply_changes = options['apply']
        adoptions = self._parse_adoptions(options['adopt_client_thread'])

        planned, skipped = [], []
        for project in Project.objects.select_related('client__profile').order_by('pk'):
            if CommunicationThread.objects.filter(managed_project=project).exists():
                continue
            profile = resolve_client_profile(project)
            if profile is None:
                skipped.append((
                    project,
                    'el cliente del proyecto no tiene un perfil de cliente utilizable',
                ))
                continue
            planned.append((project, profile))

        for project, profile in planned:
            self.stdout.write(
                f'  crear    madre de «{project.name}» (proyecto {project.pk}) '
                f'→ cliente {profile.pk}'
            )
        for project, reason in skipped:
            self.stdout.write(
                f'  saltar   proyecto {project.pk} «{project.name}» — {reason}'
            )
        for thread_id, profile_id in sorted(adoptions.items()):
            self.stdout.write(
                f'  adoptar  hilo {thread_id} como madre del cliente {profile_id}'
            )

        if not apply_changes:
            self.stdout.write(
                f'Dry-run: {len(planned)} madre(s) por crear, {len(skipped)} '
                f'saltada(s), {len(adoptions)} adopción(es). Nada se escribió. '
                'Repetí con --apply.'
            )
            return

        created = 0
        with transaction.atomic():
            for project, _profile in planned:
                if ensure_project_thread(project) is not None:
                    created += 1
            for thread_id, profile_id in sorted(adoptions.items()):
                thread = CommunicationThread.objects.get(pk=thread_id)
                profile = UserProfile.objects.clients().get(pk=profile_id)
                adopt_client_thread(thread, profile)

        self.stdout.write(self.style.SUCCESS(
            f'{created} madre(s) de proyecto creada(s); {len(adoptions)} '
            f'adopción(es) de cliente; {len(skipped)} saltada(s).'
        ))
