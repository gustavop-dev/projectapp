"""Vincula carpetas y documentos a cliente/proyecto emparejando por nombre.

La pertenencia vivía en el nombre de la carpeta (Carlos, Kore - Diseño,
G&M Project…) y no como relación. Este comando propone el emparejamiento
carpeta→proyecto/cliente por nombre normalizado y lo aplica sólo cuando es
inequívoco; lo demás queda reportado para revisión manual — el recorte
«Sin cliente» del gestor de documentos es exactamente esa lista.

El orden importa: primero se asocia la CARPETA y después sus documentos
HEREDAN de ella, en vez de emparejarse uno por uno. Una carpeta sin match
propio materializa el del ancestro más cercano (las subcarpetas de
«Kore - Diseño» son de Kore), y una carpeta que ya tiene dueño —puesto a
mano o por una corrida anterior— nunca se reescribe.

Dry-run por defecto: imprime el plan completo sin escribir nada. Con --apply
escribe en una transacción con update_fields explícitos. Idempotente: lo que
ya tiene cliente se salta siempre, así que una segunda corrida reporta 0. En
producción requiere DJANGO_SETTINGS_MODULE=projectapp.settings_prod.
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
            'normalize': 0, 'folders': 0, 'project': 0, 'client': 0,
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
        by_id = {folder.pk: folder for folder in folders}

        # ── Pass 1: la CARPETA primero ─────────────────────────────────────
        # Emparejar la carpeta y no sus documentos uno por uno es lo que hace
        # que el resto sea herencia: una carpeta asociada le da dueño a todo
        # lo que guarda (y es lo que cuenta el filtro «Con carpeta»).
        # resolved[pk] = (project|None, user|None), o None si no hay señal.
        resolved = {}
        folder_updates = []

        def resolve(folder):
            if folder.pk in resolved:
                return resolved[folder.pk]
            # Corta ciclos y sirve de centinela mientras sube por el árbol.
            resolved[folder.pk] = None
            # Una carpeta YA asociada manda: es una decisión de alguien (a
            # mano o de una corrida anterior), no una conjetura por el nombre.
            if folder.client_user_id or folder.project_id:
                value = (folder.project, folder.client_user)
                resolved[folder.pk] = value
                return value

            match = own.get(folder.pk)
            kind = match[0] if match else None
            if kind == 'ambiguous':
                summary['ambiguous'] += 1
                self.stdout.write(
                    f'[ambigua] "{folder.name}" → {len(match[1])} candidatos '
                    '— sin cambios',
                )
                return None

            if kind == 'project':
                project = projects[match[1]]
                value, source = (project, project.client), 'own'
            elif kind == 'client':
                value, source = (None, profiles[match[1]].user), 'own'
            else:
                # Las subcarpetas de «Kore - Diseño» son de Kore: sin match
                # propio se hereda el del ancestro más cercano que tenga uno.
                parent = by_id.get(folder.parent_id)
                value, source = (resolve(parent) if parent else None), 'inherited'

            resolved[folder.pk] = value
            if value is None:
                summary['unmatched'] += 1
                self.stdout.write(
                    f'[sin match] "{folder.name}" — revisión manual',
                )
                return None

            project, user = value
            profile = getattr(user, 'profile', None) if user else None
            display = build_client_display_name(profile) if profile else ''
            folder_updates.append((folder, value))
            summary['folders'] += 1
            if source == 'inherited':
                self.stdout.write(
                    f'[heredada] "{folder.name}" → toma la asociación de su '
                    f'carpeta contenedora (cliente: {display or "sin perfil"})',
                )
            elif project is not None:
                self.stdout.write(
                    f'[carpeta→proyecto] "{folder.name}" → Proyecto '
                    f'#{project.pk} "{project.name}" (cliente: '
                    f'{display or "sin perfil"})',
                )
            else:
                self.stdout.write(
                    f'[carpeta→cliente] "{folder.name}" → Cliente '
                    f'#{profile.pk} "{display}"',
                )
            return value

        for folder in folders:
            resolve(folder)

        # ── Pass 2: los documentos heredan de su carpeta ya asociada ───────
        for folder in folders:
            # Los docs con proyecto y sin cliente ya van en el pass 0; acá
            # sólo los totalmente sueltos, para no pisar un proyecto real con
            # la asociación de la carpeta.
            unlinked = list(Document.objects.filter(
                folder=folder, client_user__isnull=True, project__isnull=True,
            ))
            if not unlinked:
                continue
            value = resolved.get(folder.pk)
            if value is None:
                continue
            project, user = value
            profile = getattr(user, 'profile', None) if user else None
            display = build_client_display_name(profile) if profile else ''
            for document in unlinked:
                updates = {'client_user': user}
                if project is not None:
                    updates['project'] = project
                if not document.client_name and display:
                    updates['client_name'] = display
                pending.append((document, updates))
            summary['project' if project is not None else 'client'] += len(unlinked)
            self.stdout.write(
                f'[carpeta→documentos] "{folder.name}" — '
                f'{len(unlinked)} documento(s) heredan su asociación',
            )

        self.stdout.write(
            f'Resumen: {summary["folders"]} carpeta(s) asociadas, '
            f'{summary["project"]} documentos por proyecto, '
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
            for folder, (project, user) in folder_updates:
                folder.project = project
                folder.client_user = user
                folder.save(update_fields=['project', 'client_user', 'updated_at'])
            for document, updates in pending:
                for field, value in updates.items():
                    setattr(document, field, value)
                document.save(update_fields=[*updates.keys(), 'updated_at'])
        self.stdout.write(self.style.SUCCESS(
            f'Aplicado: {len(folder_updates)} carpeta(s) y '
            f'{len(pending)} documento(s) actualizados.',
        ))
