"""Vincula los documentos existentes a cliente/proyecto desde su carpeta.

La pertenencia vivía en el nombre de la carpeta (Carlos, Kore - Diseño,
G&M Project…) y no como relación. Este comando propone el emparejamiento
carpeta→proyecto/cliente por nombre normalizado y lo aplica sólo cuando es
inequívoco; lo demás queda reportado para revisión manual — el recorte
«Sin cliente» del gestor de documentos es exactamente esa lista.

Dry-run por defecto: imprime el plan completo sin escribir nada. Con --apply
escribe en una transacción con update_fields explícitos. Idempotente: los
documentos que ya tienen cliente se saltan siempre, así que una segunda
corrida reporta 0. En producción requiere
DJANGO_SETTINGS_MODULE=projectapp.settings_prod.
"""
import re
import unicodedata
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Project, UserProfile
from accounts.services.proposal_client_service import build_client_display_name
from content.models import Document, DocumentFolder

# Sufijos que un nombre de carpeta agrega al nombre real del proyecto
# («Vastago Proj», «G&M Project»); se quitan sólo como tokens finales.
SUFFIX_TOKENS = {'proj', 'project', 'proyecto', 'diseno', 'web'}
MIN_KEY_LENGTH = 3


def normalize_name(value):
    """Espejo Python de frontend/utils/clientMatch.js: sin acentos,
    minúsculas, sólo [a-z0-9& ] y espacios colapsados."""
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(char for char in text if not unicodedata.combining(char))
    text = text.lower()
    text = re.sub(r'[^a-z0-9& ]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def name_keys(value):
    """Variantes con las que un nombre puede matchear una carpeta.

    El nombre entero, sus mitades por ' - ' (patrón «Kore - Diseño») y cada
    una sin sufijos finales. Una clave de menos de 3 caracteres o que ES un
    sufijo no identifica nada y se descarta.
    """
    keys = set()
    raw = str(value or '')
    candidates = [normalize_name(raw)]
    candidates += [normalize_name(part) for part in raw.split(' - ')]
    for candidate in candidates:
        if not candidate or candidate in SUFFIX_TOKENS:
            continue
        if len(candidate) >= MIN_KEY_LENGTH:
            keys.add(candidate)
        tokens = candidate.split(' ')
        while len(tokens) > 1 and tokens[-1] in SUFFIX_TOKENS:
            tokens = tokens[:-1]
            stripped = ' '.join(tokens)
            if len(stripped) >= MIN_KEY_LENGTH:
                keys.add(stripped)
    return keys


class Command(BaseCommand):
    help = (
        'Asigna cliente/proyecto a los documentos existentes emparejando el '
        'nombre de su carpeta contra proyectos y clientes registrados. '
        'Dry-run por defecto; --apply escribe.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply', action='store_true',
            help='Aplica el plan (por defecto sólo se imprime).',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']

        projects = {
            project.pk: project
            for project in Project.objects.select_related('client__profile')
        }
        project_index = defaultdict(set)
        for project in projects.values():
            for key in name_keys(project.name):
                project_index[key].add(project.pk)

        profiles = {}
        client_index = defaultdict(set)
        for profile in UserProfile.objects.clients().select_related('user'):
            profiles[profile.pk] = profile
            sources = {
                build_client_display_name(profile),
                profile.company_name,
                f'{profile.user.first_name} {profile.user.last_name}',
                profile.user.first_name,
            }
            for source in sources:
                for key in name_keys(source):
                    client_index[key].add(profile.pk)

        pending = []
        summary = {
            'normalize': 0, 'project': 0, 'client': 0,
            'ambiguous': 0, 'unmatched': 0,
        }

        # ── Pass 0: documentos con proyecto y sin cliente heredan al dueño ──
        normalize_docs = list(
            Document.objects
            .filter(project__isnull=False, client_user__isnull=True)
            .select_related('project__client__profile')
        )
        for document in normalize_docs:
            updates = {'client_user': document.project.client}
            profile = getattr(document.project.client, 'profile', None)
            if not document.client_name and profile is not None:
                updates['client_name'] = build_client_display_name(profile)
            pending.append((document, updates))
        summary['normalize'] = len(normalize_docs)
        if normalize_docs:
            self.stdout.write(
                f'[normalize] {len(normalize_docs)} documento(s) con proyecto '
                'y sin cliente → heredan el cliente del proyecto',
            )

        # ── Match por carpeta. El de proyecto tiene prioridad sobre el de
        # cliente (la carpeta de un proyecto implica al cliente vía la
        # derivación); dentro de un tipo, 2+ candidatos = ambigua y no se toca.
        def own_match(folder):
            keys = name_keys(folder.name)
            project_ids = set()
            for key in keys:
                project_ids |= project_index.get(key, set())
            if len(project_ids) == 1:
                return ('project', next(iter(project_ids)))
            if len(project_ids) > 1:
                return ('ambiguous', project_ids)
            client_ids = set()
            for key in keys:
                client_ids |= client_index.get(key, set())
            if len(client_ids) == 1:
                return ('client', next(iter(client_ids)))
            if len(client_ids) > 1:
                return ('ambiguous', client_ids)
            return None

        folders = list(DocumentFolder.objects.all())
        own = {folder.pk: own_match(folder) for folder in folders}

        def effective_match(folder):
            match = own.get(folder.pk)
            if match is not None:
                return match
            # Las subcarpetas de «Kore - Diseño» son de Kore: sin match propio
            # se hereda el del ancestro más cercano que tenga uno.
            for ancestor in reversed(folder.get_ancestors()):
                match = own.get(ancestor.pk)
                if match is not None:
                    return match
            return None

        for folder in folders:
            # Los docs con proyecto y sin cliente ya van en el pass 0; acá
            # sólo los totalmente sueltos, para no pisar un proyecto real con
            # el match de la carpeta.
            unlinked = Document.objects.filter(
                folder=folder, client_user__isnull=True, project__isnull=True,
            )
            unlinked_count = unlinked.count()
            if unlinked_count == 0:
                continue
            match = effective_match(folder)
            if match is None:
                summary['unmatched'] += 1
                self.stdout.write(
                    f'[sin match] "{folder.name}" — {unlinked_count} '
                    'documento(s), revisión manual',
                )
                continue
            kind, matched = match
            if kind == 'ambiguous':
                summary['ambiguous'] += 1
                self.stdout.write(
                    f'[ambigua] "{folder.name}" → {len(matched)} candidatos '
                    '— sin cambios',
                )
                continue
            if kind == 'project':
                project = projects[matched]
                profile = getattr(project.client, 'profile', None)
                display = build_client_display_name(profile) if profile else ''
                docs = list(unlinked)
                for document in docs:
                    updates = {'project': project, 'client_user': project.client}
                    if not document.client_name and display:
                        updates['client_name'] = display
                    pending.append((document, updates))
                summary['project'] += len(docs)
                self.stdout.write(
                    f'[carpeta→proyecto] "{folder.name}" → Proyecto '
                    f'#{project.pk} "{project.name}" (cliente: '
                    f'{display or "sin perfil"}) — {len(docs)} documento(s)',
                )
            else:
                profile = profiles[matched]
                display = build_client_display_name(profile)
                docs = list(unlinked)
                for document in docs:
                    updates = {'client_user': profile.user}
                    if not document.client_name:
                        updates['client_name'] = display
                    pending.append((document, updates))
                summary['client'] += len(docs)
                self.stdout.write(
                    f'[carpeta→cliente] "{folder.name}" → Cliente '
                    f'#{profile.pk} "{display}" — {len(docs)} documento(s)',
                )

        self.stdout.write(
            f'Resumen: {summary["project"]} por proyecto, '
            f'{summary["client"]} por cliente, '
            f'{summary["normalize"]} normalizados, '
            f'{summary["ambiguous"]} ambiguas, '
            f'{summary["unmatched"]} sin match.',
        )

        if not apply_changes:
            self.stdout.write(
                'Dry-run: nada se escribió. Ejecuta con --apply para aplicar.',
            )
            return

        with transaction.atomic():
            for document, updates in pending:
                for field, value in updates.items():
                    setattr(document, field, value)
                document.save(update_fields=[*updates.keys(), 'updated_at'])
        self.stdout.write(self.style.SUCCESS(
            f'Aplicado: {len(pending)} documento(s) actualizados.',
        ))
