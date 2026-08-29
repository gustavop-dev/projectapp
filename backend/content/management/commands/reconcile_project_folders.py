"""Plan and apply the reviewed adoption of existing project folders.

Planning is always read-only. Applying requires a fully reviewed manifest, its
exact SHA-256 and an unchanged database fingerprint. The command deliberately
does not offer an ``--apply`` shortcut based on names: a suggestion is evidence
for a person to review, never authority to move documents.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import Project, UserProfile
from accounts.services.proposal_client_service import build_client_display_name
from content.management.commands.link_documents_from_folders import (
    name_keys,
    normalize_name,
)
from content.models import Document, DocumentFolder
from content.services.document_type_codes import COLLECTION_ACCOUNT
from content.services.generated_document_filing_service import (
    describe_generated_folder_path,
    ensure_generated_folder_path,
)
from content.services.project_document_folder_service import ensure_project_folder


MANIFEST_VERSION = 2
PERSONAL_ROOTS = {
    normalize_name(name)
    for name in (
        'temp', 'Carlos', 'Gustavo', 'Templates', 'Samuel', 'Gustavo CLI',
        'Familia', 'Requirement Estimates', 'ProjectApp', 'Aerocivil',
        'Kafe Sistemas Project', 'Aaron',
    )
}
EXPECTED_PROJECTLIKE_ROOTS = ('Proyegabs',)


def _iso(value):
    return value.isoformat() if value else None


def _canonical(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
    ).encode()


def _sha256(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def database_snapshot():
    """Stable source state used to reject a stale reviewed plan."""
    return {
        'projects': list(
            Project.objects.order_by('id').values(
                'id', 'name', 'client_id', 'current_state_id', 'updated_at',
            )
        ),
        'folders': list(
            DocumentFolder.objects.order_by('id').values(
                'id', 'name', 'parent_id', 'project_id', 'client_user_id',
                'managed_project_id', 'system_key', 'is_archived', 'updated_at',
            )
        ),
        'documents': list(
            Document.objects.order_by('id').values(
                'id', 'folder_id', 'project_id', 'client_user_id',
                'document_type_id', 'commercial_status', 'issue_date',
                'updated_at',
            )
        ),
    }


def _json_snapshot(snapshot):
    return {
        section: [
            {
                key: _iso(value) if key in {'updated_at', 'issue_date'} else value
                for key, value in row.items()
            }
            for row in rows
        ]
        for section, rows in snapshot.items()
    }


def _tree_ids(root, folders):
    by_parent = defaultdict(list)
    for folder in folders:
        by_parent[folder.parent_id].append(folder)
    result = []
    pending = [root.id]
    visited = set()
    while pending:
        folder_id = pending.pop()
        if folder_id in visited:
            continue
        visited.add(folder_id)
        result.append(folder_id)
        pending.extend(child.id for child in by_parent.get(folder_id, ()))
    return result


def _impact(root, project, folders, documents):
    ids = set(_tree_ids(root, folders))
    tree_folders = [folder for folder in folders if folder.id in ids]
    tree_documents = [document for document in documents if document.folder_id in ids]
    folder_conflicts = [
        folder.id for folder in tree_folders
        if (
            folder.project_id not in (None, project.id)
            or folder.client_user_id not in (None, project.client_id)
        )
    ]
    document_conflicts = [
        document.id for document in tree_documents
        if (
            document.project_id not in (None, project.id)
            or document.client_user_id not in (None, project.client_id)
        )
    ]
    return {
        'folder_count': len(tree_folders),
        'document_count': len(tree_documents),
        'folder_conflict_ids': folder_conflicts,
        'document_conflict_ids': document_conflicts,
    }


def _project_candidates(folder, projects):
    folder_keys = name_keys(folder.name)
    exact = [
        project for project in projects
        if folder_keys.intersection(name_keys(project.name))
    ]
    if exact:
        return exact, 'normalized-name'
    first_token = normalize_name(folder.name).split(' ', 1)[0]
    if len(first_token) < 4:
        return [], None
    prefixed = [
        project for project in projects
        if normalize_name(project.name).split(' ', 1)[0] == first_token
    ]
    return prefixed, 'unique-leading-token' if prefixed else None


def _root_id(folder_id, folders_by_id):
    current = folders_by_id.get(folder_id)
    visited = set()
    while current is not None and current.parent_id and current.id not in visited:
        visited.add(current.id)
        current = folders_by_id.get(current.parent_id)
    return current.id if current is not None else None


def _generated_document_path(document):
    cancelled = document.commercial_status == Document.CommercialStatus.CANCELLED
    unissued = cancelled and not document.issue_date
    if getattr(document.document_type, 'code', None) != COLLECTION_ACCOUNT:
        return None
    if not document.issue_date and not unissued:
        return None
    return describe_generated_folder_path(
        COLLECTION_ACCOUNT,
        business_date=document.issue_date,
        project=document.project,
        client_user=document.client_user,
        cancelled=cancelled,
        unissued=unissued,
    )


def build_manifest():
    projects = list(
        Project.objects.select_related('client__profile', 'current_state')
        .order_by('id')
    )
    profiles = list(UserProfile.objects.clients().select_related('user'))
    folders = list(DocumentFolder.objects.all().order_by('id'))
    documents = list(
        Document.objects.select_related(
            'document_type', 'project', 'client_user',
        ).order_by('id')
    )
    roots = [folder for folder in folders if folder.parent_id is None]
    folders_by_id = {folder.id: folder for folder in folders}
    existing_managed_by_project = {
        folder.managed_project_id: folder
        for folder in roots
        if folder.managed_project_id
    }

    profile_keys = defaultdict(set)
    profiles_by_id = {profile.id: profile for profile in profiles}
    for profile in profiles:
        for source in (
            build_client_display_name(profile), profile.company_name,
            profile.user.get_full_name(), profile.user.first_name,
        ):
            for key in name_keys(source):
                profile_keys[key].add(profile.id)

    project_by_client = defaultdict(list)
    for project in projects:
        project_by_client[project.client_id].append(project)

    actions = []
    proposed_project_ids = set()
    proposed_tree_roots = defaultdict(set)
    for root in roots:
        if root.managed_project_id:
            proposed_project_ids.add(root.managed_project_id)
            proposed_tree_roots[root.managed_project_id].add(root.id)
            actions.append({
                'id': f'existing-{root.id}',
                'type': 'existing',
                'decision': 'skip',
                'folder_id': root.id,
                'project_id': root.managed_project_id,
                'reason': 'La raíz ya está administrada por el proyecto.',
            })
            continue
        if normalize_name(root.name) in PERSONAL_ROOTS:
            actions.append({
                'id': f'leave-{root.id}', 'type': 'leave', 'decision': 'skip',
                'folder_id': root.id, 'project_id': None,
                'reason': 'Clasificada explícitamente como carpeta propia.',
            })
            continue
        candidates, rule = _project_candidates(root, projects)
        if len(candidates) == 1:
            project = candidates[0]
            existing_root = existing_managed_by_project.get(project.id)
            if existing_root is not None:
                actions.append({
                    'id': f'conflict-{root.id}', 'type': 'conflict',
                    'decision': 'pending', 'folder_id': root.id,
                    'project_id': project.id,
                    'candidate_project_ids': [project.id],
                    'reason': (
                        f'El proyecto ya tiene la raíz automática '
                        f'{existing_root.id}; revisa cómo consolidar esta '
                        'segunda carpeta sin mezclar contenido.'
                    ),
                })
                continue
            if project.id in proposed_project_ids:
                actions.append({
                    'id': f'conflict-{root.id}', 'type': 'conflict',
                    'decision': 'pending', 'folder_id': root.id,
                    'project_id': project.id,
                    'candidate_project_ids': [project.id],
                    'reason': (
                        'Otra carpeta ya fue propuesta como raíz de este '
                        'proyecto; sólo una puede convertirse.'
                    ),
                })
                continue
            if root.is_archived:
                actions.append({
                    'id': f'conflict-{root.id}', 'type': 'conflict',
                    'decision': 'pending', 'folder_id': root.id,
                    'project_id': project.id,
                    'candidate_project_ids': [project.id],
                    'reason': (
                        'La carpeta candidata está archivada. Restáurala y '
                        'regenera la propuesta antes de convertirla.'
                    ),
                })
                continue
            proposed_project_ids.add(project.id)
            proposed_tree_roots[project.id].add(root.id)
            actions.append({
                'id': f'convert-{root.id}-{project.id}',
                'type': 'convert',
                'decision': 'pending',
                'folder_id': root.id,
                'folder_name': root.name,
                'project_id': project.id,
                'project_name': project.name,
                'rename_to': project.name,
                'rule': rule,
                'impact': _impact(root, project, folders, documents),
            })
            continue
        if len(candidates) > 1:
            actions.append({
                'id': f'conflict-{root.id}', 'type': 'conflict',
                'decision': 'pending', 'folder_id': root.id,
                'project_id': None,
                'candidate_project_ids': [project.id for project in candidates],
                'reason': 'Más de un proyecto coincide con el nombre.',
            })
            continue

        matching_profiles = set()
        for key in name_keys(root.name):
            matching_profiles.update(profile_keys.get(key, ()))
        client_projects = []
        if len(matching_profiles) == 1:
            profile = profiles_by_id[next(iter(matching_profiles))]
            client_projects = project_by_client.get(profile.user_id, [])
        if len(client_projects) == 1:
            project = client_projects[0]
            proposed_tree_roots[project.id].add(root.id)
            actions.append({
                'id': f'nest-{root.id}-{project.id}',
                'type': 'nest_client_folder',
                'decision': 'pending',
                'folder_id': root.id,
                'folder_name': root.name,
                'project_id': project.id,
                'project_name': project.name,
                'rule': 'client-with-single-project',
                'impact': _impact(root, project, folders, documents),
            })
            continue
        actions.append({
            'id': f'leave-{root.id}', 'type': 'leave', 'decision': 'skip',
            'folder_id': root.id, 'project_id': None,
            'reason': 'No existe un proyecto inequívoco; permanece como propia.',
        })

    for project in projects:
        if project.id in proposed_project_ids:
            continue
        actions.append({
            'id': f'create-{project.id}',
            'type': 'create',
            'decision': 'pending',
            'folder_id': None,
            'project_id': project.id,
            'project_name': project.name,
            'state': project.current_state.name if project.current_state else None,
            'visible_by_default': bool(
                project.current_state
                and project.current_state.show_in_document_manager
            ),
            'reason': 'El proyecto no tiene una raíz existente propuesta.',
        })

    for document in documents:
        if not document.project_id:
            continue
        current_root_id = _root_id(document.folder_id, folders_by_id)
        if current_root_id in proposed_tree_roots[document.project_id]:
            continue
        if document.folder_id is not None:
            actions.append({
                'id': f'document-conflict-{document.id}',
                'type': 'document_conflict',
                'decision': 'pending',
                'document_id': document.id,
                'document_title': document.title,
                'folder_id': document.folder_id,
                'project_id': document.project_id,
                'project_name': document.project.name,
                'reason': (
                    'El documento apunta al proyecto, pero está dentro de otra '
                    'raíz manual. Revisa su ubicación; no se moverá por inferencia.'
                ),
            })
            continue
        target_path = _generated_document_path(document)
        if target_path is None:
            actions.append({
                'id': f'document-conflict-{document.id}',
                'type': 'document_conflict',
                'decision': 'pending',
                'document_id': document.id,
                'document_title': document.title,
                'folder_id': None,
                'project_id': document.project_id,
                'project_name': document.project.name,
                'reason': (
                    'El documento tiene proyecto pero no una ruta automática '
                    'inequívoca; permanece sin carpeta hasta revisión manual.'
                ),
            })
            continue
        actions.append({
            'id': f'file-document-{document.id}',
            'type': 'file_document',
            'decision': 'pending',
            'document_id': document.id,
            'document_title': document.title,
            'folder_id': None,
            'project_id': document.project_id,
            'project_name': document.project.name,
            'target_path': target_path,
            'reason': f'Ubicación propuesta: {target_path}.',
        })

    snapshot = _json_snapshot(database_snapshot())
    existing_names = {normalize_name(folder.name) for folder in folders}
    return {
        'version': MANIFEST_VERSION,
        'generated_at': timezone.now().isoformat(),
        'database_fingerprint': _sha256(snapshot),
        'review_instructions': (
            'Cambia decision a approve o skip en cada acción pendiente. '
            'Ninguna acción pendiente permite aplicar el manifiesto.'
        ),
        'missing_expected_names': [
            name for name in EXPECTED_PROJECTLIKE_ROOTS
            if normalize_name(name) not in existing_names
        ],
        'actions': actions,
    }


def _markdown_report(manifest):
    lines = [
        '# Propuesta de carpetas de proyecto', '',
        f'- Generada: {manifest["generated_at"]}',
        f'- Huella de datos: `{manifest["database_fingerprint"]}`',
        '',
        '| Decisión | Acción | Carpeta | Proyecto | Motivo/impacto |',
        '|---|---|---|---|---|',
    ]
    for action in manifest['actions']:
        impact = action.get('impact') or {}
        detail = action.get('reason') or (
            f'{impact.get("folder_count", 0)} carpetas; '
            f'{impact.get("document_count", 0)} documentos; '
            f'{len(impact.get("folder_conflict_ids", [])) + len(impact.get("document_conflict_ids", []))} conflictos'
        )
        lines.append(
            f'| {action["decision"]} | {action["type"]} | '
            f'{action.get("folder_name") or action.get("document_title") or action.get("folder_id") or "—"} | '
            f'{action.get("project_name") or action.get("project_id") or "—"} | '
            f'{detail} |'
        )
    if manifest['missing_expected_names']:
        lines.extend([
            '', '## Nombres esperados ausentes', '',
            *[f'- {name}' for name in manifest['missing_expected_names']],
        ])
    return '\n'.join(lines) + '\n'


def _validate_review(manifest):
    if manifest.get('version') != MANIFEST_VERSION:
        raise CommandError('La versión del manifiesto no es compatible.')
    invalid = [
        action['id'] for action in manifest.get('actions', [])
        if action.get('decision') not in {'approve', 'skip'}
    ]
    if invalid:
        raise CommandError(
            'La revisión está incompleta; quedan decisiones pendientes: '
            + ', '.join(invalid)
        )
    invalid_approvals = [
        action['id'] for action in manifest.get('actions', [])
        if action.get('decision') == 'approve'
        and action.get('type') not in {
            'convert', 'create', 'nest_client_folder', 'file_document',
        }
    ]
    if invalid_approvals:
        raise CommandError(
            'Estas filas son informativas y sólo admiten skip: '
            + ', '.join(invalid_approvals)
        )


def _assert_no_conflicts(action):
    impact = action.get('impact') or {}
    conflicts = (
        impact.get('folder_conflict_ids', [])
        + impact.get('document_conflict_ids', [])
    )
    if conflicts:
        raise CommandError(
            f'La acción {action["id"]} conserva asociaciones contradictorias. '
            'Resuélvelas, regenera el manifiesto y vuelve a revisarlo.'
        )


def _associate_tree(root, project):
    folder_ids = {root.id, *root.get_descendant_ids()}
    folders = DocumentFolder.objects.filter(pk__in=folder_ids)
    conflicting_folders = folders.exclude(
        (Q(project__isnull=True) | Q(project_id=project.id))
        & (
            Q(client_user__isnull=True)
            | Q(client_user_id=project.client_id)
        )
    )
    if conflicting_folders.exists():
        raise CommandError('La jerarquía cambió y ahora contiene carpetas ajenas.')
    documents = Document.objects.filter(folder_id__in=folder_ids)
    conflicting_documents = documents.exclude(
        (Q(project__isnull=True) | Q(project_id=project.id))
        & (
            Q(client_user__isnull=True)
            | Q(client_user_id=project.client_id)
        )
    )
    if conflicting_documents.exists():
        raise CommandError('La jerarquía cambió y ahora contiene documentos ajenos.')
    folders.update(project=project, client_user=project.client)
    documents.filter(project__isnull=True).update(project=project)
    documents.filter(client_user__isnull=True).update(client_user=project.client)


def _file_reviewed_document(action, inverse):
    document = Document.objects.select_related(
        'document_type', 'project', 'client_user',
    ).get(pk=action['document_id'])
    if document.project_id != action['project_id'] or document.folder_id is not None:
        raise CommandError(
            f'El documento {document.id} cambió desde el plan de ubicación.'
        )
    if document.client_user_id not in (None, document.project.client_id):
        raise CommandError(
            f'El documento {document.id} pertenece a otro cliente.'
        )
    try:
        document.project.document_root_folder
    except DocumentFolder.DoesNotExist as exc:
        raise CommandError(
            f'El proyecto {document.project_id} no tiene una raíz aprobada.'
        ) from exc
    target_path = _generated_document_path(document)
    if target_path is None or target_path != action.get('target_path'):
        raise CommandError(
            f'La ruta canónica del documento {document.id} cambió desde el plan.'
        )

    previous_folder_ids = set(
        DocumentFolder.objects.values_list('id', flat=True)
    )
    cancelled = document.commercial_status == Document.CommercialStatus.CANCELLED
    target = ensure_generated_folder_path(
        COLLECTION_ACCOUNT,
        business_date=document.issue_date,
        project=document.project,
        client_user=document.client_user,
        cancelled=cancelled,
        unissued=cancelled and not document.issue_date,
    )
    inverse['changes'].append({
        'type': 'filed_document',
        'document_id': document.id,
        'folder_id': document.folder_id,
        'client_user_id': document.client_user_id,
        'created_folder_ids': sorted(
            set(DocumentFolder.objects.values_list('id', flat=True))
            - previous_folder_ids
        ),
    })
    document.folder = target
    update_fields = ['folder', 'updated_at']
    if document.client_user_id is None:
        document.client_user = document.project.client
        update_fields.append('client_user')
    document.save(update_fields=update_fields)


@transaction.atomic
def apply_manifest(manifest):
    list(Project.objects.select_for_update().values_list('id', flat=True))
    list(DocumentFolder.objects.select_for_update().values_list('id', flat=True))
    list(Document.objects.select_for_update().values_list('id', flat=True))
    current_fingerprint = _sha256(_json_snapshot(database_snapshot()))
    if current_fingerprint != manifest.get('database_fingerprint'):
        raise CommandError(
            'Los proyectos, carpetas o documentos cambiaron desde el plan. '
            'Regenera y revisa un manifiesto nuevo.'
        )
    inverse = {'version': 1, 'generated_at': timezone.now().isoformat(), 'changes': []}

    approved = [
        action for action in manifest['actions']
        if action['decision'] == 'approve'
    ]
    for action in approved:
        if action['type'] not in {'convert', 'create'}:
            continue
        project = Project.objects.get(pk=action['project_id'])
        if action['type'] == 'create':
            root = ensure_project_folder(project)
            inverse['changes'].append({
                'type': 'created_tree', 'root_id': root.id,
                'project_id': project.id,
            })
            continue
        _assert_no_conflicts(action)
        root = DocumentFolder.objects.get(pk=action['folder_id'])
        if root.parent_id is not None or root.managed_project_id is not None:
            raise CommandError(f'La carpeta {root.id} ya no es una raíz manual.')
        if DocumentFolder.objects.filter(managed_project=project).exists():
            raise CommandError(f'El proyecto {project.id} ya tiene una raíz.')
        inverse['changes'].append({
            'type': 'converted', 'folder_id': root.id,
            'name': root.name, 'parent_id': root.parent_id,
            'project_id': root.project_id, 'client_user_id': root.client_user_id,
            'managed_project_id': root.managed_project_id,
        })
        root.name = project.name
        root.project = project
        root.client_user = project.client
        root.managed_project = project
        root.save(update_fields=[
            'name', 'project', 'client_user', 'managed_project', 'updated_at',
        ])
        _associate_tree(root, project)

    for action in approved:
        if action['type'] != 'nest_client_folder':
            continue
        _assert_no_conflicts(action)
        project = Project.objects.get(pk=action['project_id'])
        try:
            project_root = project.document_root_folder
        except DocumentFolder.DoesNotExist as exc:
            raise CommandError(
                f'El proyecto {project.id} no tiene una raíz aprobada.'
            ) from exc
        folder = DocumentFolder.objects.get(pk=action['folder_id'])
        inverse['changes'].append({
            'type': 'nested', 'folder_id': folder.id,
            'parent_id': folder.parent_id, 'project_id': folder.project_id,
            'client_user_id': folder.client_user_id,
        })
        folder.parent = project_root
        folder.project = project
        folder.client_user = project.client
        folder.save(update_fields=[
            'parent', 'project', 'client_user', 'updated_at',
        ])
        _associate_tree(folder, project)
    for action in approved:
        if action['type'] == 'file_document':
            _file_reviewed_document(action, inverse)
    return inverse


class Command(BaseCommand):
    help = (
        'Genera una propuesta revisable o aplica un manifiesto aprobado para '
        'distinguir raíces automáticas de proyecto. Nunca aplica por nombre.'
    )

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument('--plan', metavar='JSON_PATH')
        mode.add_argument('--apply-reviewed', metavar='JSON_PATH')
        parser.add_argument('--confirm', help='SHA-256 exacto del manifiesto revisado.')
        parser.add_argument('--inverse-out', help='Ruta del snapshot inverso generado.')

    def handle(self, *args, **options):
        if options['plan']:
            output = Path(options['plan']).expanduser().resolve()
            manifest = build_manifest()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            report = output.with_suffix('.md')
            report.write_text(_markdown_report(manifest), encoding='utf-8')
            file_hash = hashlib.sha256(output.read_bytes()).hexdigest()
            self.stdout.write(f'Manifiesto: {output}')
            self.stdout.write(f'Reporte: {report}')
            self.stdout.write(f'SHA-256: {file_hash}')
            self.stdout.write('Dry-run: nada se escribió en la base de datos.')
            return

        reviewed = Path(options['apply_reviewed']).expanduser().resolve()
        if not reviewed.exists():
            raise CommandError(f'No existe el manifiesto: {reviewed}')
        actual_hash = hashlib.sha256(reviewed.read_bytes()).hexdigest()
        if not options['confirm'] or options['confirm'] != actual_hash:
            raise CommandError(
                f'Confirmación inválida. SHA-256 esperado: {actual_hash}'
            )
        manifest = json.loads(reviewed.read_text(encoding='utf-8'))
        _validate_review(manifest)
        inverse = apply_manifest(manifest)
        inverse_path = Path(
            options['inverse_out'] or reviewed.with_suffix('.inverse.json')
        ).expanduser().resolve()
        inverse_path.write_text(
            json.dumps(inverse, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )
        self.stdout.write(self.style.SUCCESS(
            f'Manifiesto aplicado. Snapshot inverso: {inverse_path}'
        ))
