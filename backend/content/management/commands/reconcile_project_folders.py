"""Plan and apply the reviewed adoption of existing project folders.

Planning is always read-only. Applying requires a fully reviewed manifest, its
exact SHA-256 and an unchanged database fingerprint. The command deliberately
does not offer an ``--apply`` shortcut based on names: a suggestion is evidence
for a person to review, never authority to move documents.
"""
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from accounts.models import Project, UserProfile
from accounts.services.project_catalog_service import project_catalog_bucket
from accounts.services.proposal_client_service import build_client_display_name
from content.management.commands.link_documents_from_folders import (
    name_keys,
    normalize_name,
)
from content.models import Document, DocumentFolder, DocumentState, DocumentType
from content.services.document_type_codes import COLLECTION_ACCOUNT
from content.services.generated_document_filing_service import (
    describe_generated_folder_path,
    ensure_generated_folder_path,
)
from content.services.project_document_folder_service import ensure_project_folder


MANIFEST_VERSION = 5
EXPECTED_PROJECTLIKE_ROOTS = ('Proyegabs',)


def _iso(value):
    return value.isoformat() if value else None


def _canonical(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
    ).encode()


def _sha256(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _write_json_atomic(path, payload):
    """Persist an artifact without ever replacing a valid file partially."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f'.{path.name}.{os.getpid()}.tmp')
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + '\n'
    try:
        with temporary.open('w', encoding='utf-8') as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _parse_client_root_assignments(values):
    assignments = {}
    for value in values:
        try:
            folder_raw, profile_raw = value.split(':', 1)
            folder_id = int(folder_raw)
            profile_id = int(profile_raw)
        except (AttributeError, TypeError, ValueError) as exc:
            raise CommandError(
                '--assign-client-root usa el formato CARPETA:PERFIL.'
            ) from exc
        if folder_id <= 0 or profile_id <= 0:
            raise CommandError(
                '--assign-client-root requiere identificadores positivos.'
            )
        previous = assignments.get(folder_id)
        if previous is not None and previous != profile_id:
            raise CommandError(
                f'La carpeta {folder_id} tiene dos clientes distintos.'
            )
        assignments[folder_id] = profile_id
    return assignments


def _parse_project_root_nestings(values):
    nestings = {}
    for value in values:
        try:
            folder_raw, project_raw = value.split(':', 1)
            folder_id = int(folder_raw)
            project_id = int(project_raw)
        except (AttributeError, TypeError, ValueError) as exc:
            raise CommandError(
                '--nest-project-root usa el formato CARPETA:PROYECTO.'
            ) from exc
        if folder_id <= 0 or project_id <= 0:
            raise CommandError(
                '--nest-project-root requiere identificadores positivos.'
            )
        previous = nestings.get(folder_id)
        if previous is not None and previous != project_id:
            raise CommandError(
                f'La carpeta {folder_id} tiene dos proyectos distintos.'
            )
        nestings[folder_id] = project_id
    return nestings


def _parse_document_project_assignments(values):
    assignments = {}
    for value in values:
        try:
            document_raw, project_raw = value.split(':', 1)
            document_id = int(document_raw)
            project_id = int(project_raw)
        except (AttributeError, TypeError, ValueError) as exc:
            raise CommandError(
                '--assign-document-project usa el formato DOCUMENTO:PROYECTO.'
            ) from exc
        if document_id <= 0 or project_id <= 0:
            raise CommandError(
                '--assign-document-project requiere identificadores positivos.'
            )
        previous = assignments.get(document_id)
        if previous is not None and previous != project_id:
            raise CommandError(
                f'El documento {document_id} tiene dos proyectos distintos.'
            )
        assignments[document_id] = project_id
    return assignments


def database_snapshot():
    """Stable source state used to reject a stale reviewed plan."""
    return {
        'clients': list(
            UserProfile.objects.clients().order_by('id').values(
                'id', 'user_id', 'company_name', 'archived_at',
                'updated_at', 'user__first_name', 'user__last_name',
                'user__email',
            )
        ),
        'projects': list(
            Project.objects.order_by('id').values(
                'id', 'name', 'client_id', 'status', 'current_state_id',
                'current_state__operational_effect',
                'current_state__updated_at', 'updated_at',
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
                'document_type_id', 'document_type__code',
                'document_type__updated_at', 'commercial_status',
                'issue_date', 'is_archived', 'updated_at',
            )
        ),
    }


def _json_snapshot(snapshot):
    return {
        section: [
            {
                key: _iso(value) if hasattr(value, 'isoformat') else value
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


def _client_impact(root, profile, folders, documents):
    ids = set(_tree_ids(root, folders))
    tree_folders = [folder for folder in folders if folder.id in ids]
    tree_documents = [document for document in documents if document.folder_id in ids]
    return {
        'folder_count': len(tree_folders),
        'document_count': len(tree_documents),
        'folder_conflict_ids': [
            folder.id for folder in tree_folders
            if folder.project_id is not None
            or folder.client_user_id not in (None, profile.user_id)
        ],
        'document_conflict_ids': [
            document.id for document in tree_documents
            if document.project_id is not None
            or document.client_user_id not in (None, profile.user_id)
        ],
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


def _client_candidates(folder, profile_keys):
    keys = name_keys(folder.name)
    exact = set()
    for key in keys:
        exact.update(profile_keys.get(key, ()))
    if exact:
        return exact, 'normalized-name'
    first_token = normalize_name(folder.name).split(' ', 1)[0]
    if len(first_token) < 4:
        return set(), None
    prefixed = set(profile_keys.get(first_token, ()))
    return prefixed, 'unique-leading-token' if prefixed else None


def _root_id(folder_id, folders_by_id):
    current = folders_by_id.get(folder_id)
    visited = set()
    while current is not None and current.parent_id and current.id not in visited:
        visited.add(current.id)
        current = folders_by_id.get(current.parent_id)
    return current.id if current is not None else None


def _generated_document_path(document, *, project=None, client_user=None):
    cancelled = document.commercial_status == Document.CommercialStatus.CANCELLED
    unissued = cancelled and not document.issue_date
    if getattr(document.document_type, 'code', None) != COLLECTION_ACCOUNT:
        return None
    if not document.issue_date and not unissued:
        return None
    return describe_generated_folder_path(
        COLLECTION_ACCOUNT,
        business_date=document.issue_date,
        project=project or document.project,
        client_user=client_user or document.client_user,
        cancelled=cancelled,
        unissued=unissued,
    )


def _reviewed_document_target(document, project):
    client_user = document.client_user or project.client
    generated_path = _generated_document_path(
        document,
        project=project,
        client_user=client_user,
    )
    if generated_path is not None:
        return 'generated_path', generated_path
    return 'project_root', f'Proyectos / {project.name}'


def build_manifest(
    *,
    project_root_nestings=None,
    client_root_assignments=None,
    document_project_assignments=None,
):
    project_root_nestings = {
        int(folder_id): int(project_id)
        for folder_id, project_id in (project_root_nestings or {}).items()
    }
    client_root_assignments = {
        int(folder_id): int(profile_id)
        for folder_id, profile_id in (client_root_assignments or {}).items()
    }
    document_project_assignments = {
        int(document_id): int(project_id)
        for document_id, project_id in (
            document_project_assignments or {}
        ).items()
    }
    overlap = set(project_root_nestings) & set(client_root_assignments)
    if overlap:
        raise CommandError(
            'Una carpeta no puede anidarse en un proyecto y asignarse a un cliente: '
            + ', '.join(str(value) for value in sorted(overlap))
        )

    initial_snapshot = _json_snapshot(database_snapshot())
    initial_fingerprint = _sha256(initial_snapshot)

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

    projects_by_id = {project.id: project for project in projects}
    documents_by_id = {document.id: document for document in documents}
    directed_project_ids = (
        set(project_root_nestings.values())
        | set(document_project_assignments.values())
    )
    unknown_projects = directed_project_ids - set(projects_by_id)
    if unknown_projects:
        raise CommandError(
            'No existen los proyectos indicados: '
            + ', '.join(str(value) for value in sorted(unknown_projects))
        )

    eligible_projects = projects

    profile_keys = defaultdict(set)
    profiles_by_id = {profile.id: profile for profile in profiles}
    for profile in profiles:
        for source in (
            build_client_display_name(profile), profile.company_name,
            profile.user.get_full_name(), profile.user.first_name,
        ):
            for key in name_keys(source):
                profile_keys[key].add(profile.id)

    directed_folder_ids = set(client_root_assignments) | set(project_root_nestings)
    unknown_folders = directed_folder_ids - set(folders_by_id)
    if unknown_folders:
        raise CommandError(
            'No existen las carpetas indicadas: '
            + ', '.join(str(value) for value in sorted(unknown_folders))
        )
    non_root_folders = directed_folder_ids - {
        folder.id for folder in roots
    }
    if non_root_folders:
        raise CommandError(
            'Las directivas de conciliación sólo aceptan carpetas raíz: '
            + ', '.join(str(value) for value in sorted(non_root_folders))
        )
    managed_directives = {
        folder_id for folder_id in directed_folder_ids
        if folders_by_id[folder_id].managed_project_id is not None
    }
    if managed_directives:
        raise CommandError(
            'Las carpetas ya gestionadas no admiten directivas de conciliación: '
            + ', '.join(str(value) for value in sorted(managed_directives))
        )
    archived_directives = {
        folder_id for folder_id in directed_folder_ids
        if folders_by_id[folder_id].is_archived
    }
    if archived_directives:
        raise CommandError(
            'Restaura estas carpetas antes de conciliarlas: '
            + ', '.join(str(value) for value in sorted(archived_directives))
        )
    unknown_profiles = set(client_root_assignments.values()) - set(profiles_by_id)
    if unknown_profiles:
        raise CommandError(
            'No existen los perfiles de cliente indicados: '
            + ', '.join(str(value) for value in sorted(unknown_profiles))
        )

    unknown_documents = set(document_project_assignments) - set(documents_by_id)
    if unknown_documents:
        raise CommandError(
            'No existen los documentos indicados: '
            + ', '.join(str(value) for value in sorted(unknown_documents))
        )
    placed_documents = [
        document_id
        for document_id in document_project_assignments
        if documents_by_id[document_id].folder_id is not None
    ]
    if placed_documents:
        raise CommandError(
            'Sólo se pueden asignar documentos sin carpeta: '
            + ', '.join(str(value) for value in sorted(placed_documents))
        )
    linked_documents = [
        document_id
        for document_id in document_project_assignments
        if documents_by_id[document_id].project_id is not None
    ]
    if linked_documents:
        raise CommandError(
            'Sólo se pueden asignar documentos sin proyecto: '
            + ', '.join(str(value) for value in sorted(linked_documents))
        )
    client_conflicting_documents = [
        document_id
        for document_id, project_id in document_project_assignments.items()
        if documents_by_id[document_id].client_user_id not in (
            None,
            projects_by_id[project_id].client_id,
        )
    ]
    if client_conflicting_documents:
        raise CommandError(
            'Estos documentos pertenecen a otro cliente: '
            + ', '.join(
                str(value) for value in sorted(client_conflicting_documents)
            )
        )

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

        if root.id in project_root_nestings:
            # Added after the canonical managed root has been resolved.
            continue

        explicit_profile_id = client_root_assignments.get(root.id)
        if explicit_profile_id is not None:
            profile = profiles_by_id[explicit_profile_id]
            actions.append({
                'id': f'assign-client-{root.id}-{profile.id}',
                'type': 'assign_client_folder',
                'decision': 'pending',
                'folder_id': root.id,
                'folder_name': root.name,
                'project_id': None,
                'client_profile_id': profile.id,
                'client_user_id': profile.user_id,
                'client_name': build_client_display_name(profile),
                'rule': 'explicit-reviewed-directive',
                'impact': _client_impact(root, profile, folders, documents),
            })
            continue

        candidates, rule = _project_candidates(root, eligible_projects)
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

        matching_profiles, client_rule = _client_candidates(root, profile_keys)
        if len(matching_profiles) == 1:
            profile = profiles_by_id[next(iter(matching_profiles))]
            impact = _client_impact(root, profile, folders, documents)
            already_associated = (
                root.project_id is None
                and root.client_user_id == profile.user_id
                and not impact['folder_conflict_ids']
                and not impact['document_conflict_ids']
            )
            actions.append({
                'id': f'client-{root.id}-{profile.id}',
                'type': (
                    'existing_client_folder'
                    if already_associated else 'assign_client_folder'
                ),
                'decision': 'skip' if already_associated else 'pending',
                'folder_id': root.id,
                'folder_name': root.name,
                'project_id': None,
                'client_profile_id': profile.id,
                'client_user_id': profile.user_id,
                'client_name': build_client_display_name(profile),
                'rule': client_rule,
                'impact': impact,
            })
            continue
        if len(matching_profiles) > 1:
            actions.append({
                'id': f'client-conflict-{root.id}',
                'type': 'client_conflict',
                'decision': 'pending',
                'folder_id': root.id,
                'folder_name': root.name,
                'project_id': None,
                'candidate_client_profile_ids': sorted(matching_profiles),
                'reason': (
                    'Más de un cliente coincide. Regenera el plan con '
                    '--assign-client-root CARPETA:PERFIL para decidirlo.'
                ),
            })
            continue
        actions.append({
            'id': f'leave-{root.id}', 'type': 'leave', 'decision': 'skip',
            'folder_id': root.id, 'project_id': None,
            'reason': (
                'No existe un proyecto ni cliente inequívoco; permanece '
                'como carpeta sin asignar.'
            ),
        })

    for project in eligible_projects:
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
            'catalog_bucket': project_catalog_bucket(project),
            'reason': 'El proyecto no tiene una raíz existente propuesta.',
        })

    project_root_action = {
        action['project_id']: action
        for action in actions
        if action['type'] in {'existing', 'convert', 'create'}
    }
    for folder_id, project_id in sorted(project_root_nestings.items()):
        root = folders_by_id[folder_id]
        project = projects_by_id[project_id]
        target = project_root_action[project_id]
        proposed_tree_roots[project_id].add(root.id)
        actions.append({
            'id': f'nest-project-root-{root.id}-{project.id}',
            'type': 'nest_project_root',
            'decision': 'pending',
            'folder_id': root.id,
            'folder_name': root.name,
            'project_id': project.id,
            'project_name': project.name,
            'target_root_folder_id': target.get('folder_id'),
            'target_root_action_id': target['id'],
            'rule': 'explicit-reviewed-directive',
            'impact': _impact(root, project, folders, documents),
            'reason': (
                f'Anidar la raíz {root.id} dentro de la raíz gestionada de '
                f'{project.name}, conservando su nombre y contenido.'
            ),
        })

    for document_id, project_id in sorted(document_project_assignments.items()):
        document = documents_by_id[document_id]
        project = projects_by_id[project_id]
        target_strategy, target_path = _reviewed_document_target(
            document,
            project,
        )
        target_root = project_root_action[project_id]
        actions.append({
            'id': f'assign-document-project-{document.id}-{project.id}',
            'type': 'assign_document_project',
            'decision': 'pending',
            'document_id': document.id,
            'document_title': document.title,
            'folder_id': None,
            'current_project_id': None,
            'current_client_user_id': document.client_user_id,
            'project_id': project.id,
            'project_name': project.name,
            'client_user_id': project.client_id,
            'target_strategy': target_strategy,
            'target_path': target_path,
            'target_root_folder_id': target_root.get('folder_id'),
            'target_root_action_id': target_root['id'],
            'rule': 'explicit-reviewed-directive',
            'reason': (
                f'Asociar al proyecto {project.name} y ubicar en '
                f'{target_path}.'
            ),
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
    database_fingerprint = _sha256(snapshot)
    if database_fingerprint != initial_fingerprint:
        raise CommandError(
            'Los proyectos, clientes, carpetas o documentos cambiaron mientras '
            'se generaba el plan. Vuelve a generarlo antes de revisarlo.'
        )
    existing_names = {normalize_name(folder.name) for folder in folders}
    return {
        'version': MANIFEST_VERSION,
        'generated_at': timezone.now().isoformat(),
        'database_fingerprint': database_fingerprint,
        'review_instructions': (
            'Cambia decision a approve o skip en cada acción pendiente. '
            'Ninguna acción pendiente permite aplicar el manifiesto.'
        ),
        'planning_directives': {
            'project_root_nestings': [
                {
                    'folder_id': folder_id,
                    'project_id': project_id,
                }
                for folder_id, project_id in sorted(project_root_nestings.items())
            ],
            'client_root_assignments': [
                {
                    'folder_id': folder_id,
                    'client_profile_id': profile_id,
                }
                for folder_id, profile_id in sorted(
                    client_root_assignments.items()
                )
            ],
            'document_project_assignments': [
                {
                    'document_id': document_id,
                    'project_id': project_id,
                }
                for document_id, project_id in sorted(
                    document_project_assignments.items()
                )
            ],
        },
        'missing_expected_names': [
            name for name in EXPECTED_PROJECTLIKE_ROOTS
            if normalize_name(name) not in existing_names
        ],
        'actions': actions,
    }


def _markdown_report(manifest):
    lines = [
        '# Propuesta de conciliación del Gestor Documental', '',
        f'- Generada: {manifest["generated_at"]}',
        f'- Huella de datos: `{manifest["database_fingerprint"]}`',
        '',
        '| Decisión | Acción | Carpeta | Proyecto/cliente | Motivo/impacto |',
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
            f'{action.get("project_name") or action.get("client_name") or action.get("project_id") or "—"} | '
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
            'convert', 'create', 'nest_project_root',
            'assign_client_folder', 'file_document',
            'assign_document_project',
        }
    ]
    if invalid_approvals:
        raise CommandError(
            'Estas filas son informativas y sólo admiten skip: '
            + ', '.join(invalid_approvals)
        )
    invalid_nestings = [
        action['id'] for action in manifest.get('actions', [])
        if action.get('type') == 'nest_project_root'
        and not isinstance(action.get('project_id'), int)
    ]
    if invalid_nestings:
        raise CommandError(
            'Anidamientos de proyecto inválidos: '
            + ', '.join(invalid_nestings)
        )
    actions_by_id = {
        action.get('id'): action for action in manifest.get('actions', [])
    }
    missing_nesting_targets = [
        action['id'] for action in manifest.get('actions', [])
        if action.get('type') == 'nest_project_root'
        and (
            action.get('target_root_action_id') not in actions_by_id
            or (
                actions_by_id[action['target_root_action_id']].get('type')
                in {'convert', 'create'}
                and actions_by_id[action['target_root_action_id']].get('decision')
                != 'approve'
                and action.get('decision') == 'approve'
            )
        )
    ]
    if missing_nesting_targets:
        raise CommandError(
            'Cada anidamiento aprobado requiere aprobar su raíz de proyecto: '
            + ', '.join(missing_nesting_targets)
        )
    invalid_client_assignments = [
        action['id'] for action in manifest.get('actions', [])
        if action.get('type') == 'assign_client_folder'
        and not isinstance(action.get('client_profile_id'), int)
    ]
    if invalid_client_assignments:
        raise CommandError(
            'Asignaciones de cliente inválidas: '
            + ', '.join(invalid_client_assignments)
        )
    invalid_document_assignments = [
        action['id'] for action in manifest.get('actions', [])
        if action.get('type') == 'assign_document_project'
        and (
            not isinstance(action.get('document_id'), int)
            or not isinstance(action.get('project_id'), int)
            or action.get('target_strategy') not in {
                'generated_path', 'project_root',
            }
        )
    ]
    if invalid_document_assignments:
        raise CommandError(
            'Asignaciones documento→proyecto inválidas: '
            + ', '.join(invalid_document_assignments)
        )
    missing_document_targets = [
        action['id'] for action in manifest.get('actions', [])
        if action.get('type') == 'assign_document_project'
        and action.get('decision') == 'approve'
        and (
            action.get('target_root_action_id') not in actions_by_id
            or (
                actions_by_id[action['target_root_action_id']].get('type')
                in {'convert', 'create'}
                and actions_by_id[
                    action['target_root_action_id']
                ].get('decision') != 'approve'
            )
        )
    ]
    if missing_document_targets:
        raise CommandError(
            'Cada documento aprobado requiere aprobar su raíz de proyecto: '
            + ', '.join(missing_document_targets)
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


def _associate_client_tree(root, profile):
    folder_ids = {root.id, *root.get_descendant_ids()}
    folders = DocumentFolder.objects.filter(pk__in=folder_ids)
    allowed = Q(project__isnull=True) & (
        Q(client_user__isnull=True) | Q(client_user_id=profile.user_id)
    )
    conflicting_folders = folders.exclude(allowed)
    if conflicting_folders.exists():
        raise CommandError('La jerarquía cambió y ahora contiene carpetas ajenas.')
    documents = Document.objects.filter(folder_id__in=folder_ids)
    conflicting_documents = documents.exclude(allowed)
    if conflicting_documents.exists():
        raise CommandError('La jerarquía cambió y ahora contiene documentos ajenos.')
    folders.filter(client_user__isnull=True).update(client_user=profile.user)
    documents.filter(client_user__isnull=True).update(client_user=profile.user)
    display_name = build_client_display_name(profile)
    documents.filter(client_name='').update(client_name=display_name)


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


def _assign_reviewed_document_project(action, inverse):
    document = Document.objects.select_related(
        'document_type', 'project', 'client_user',
    ).get(pk=action['document_id'])
    project = Project.objects.select_related('client').get(
        pk=action['project_id'],
    )
    if document.folder_id is not None or document.project_id is not None:
        raise CommandError(
            f'El documento {document.id} cambió desde la asignación revisada.'
        )
    if document.client_user_id not in (None, project.client_id):
        raise CommandError(
            f'El documento {document.id} pertenece a otro cliente.'
        )
    root = DocumentFolder.objects.filter(
        managed_project=project,
        parent__isnull=True,
        is_archived=False,
    ).first()
    if root is None:
        raise CommandError(
            f'El proyecto {project.id} no tiene una raíz aprobada.'
        )

    target_strategy, target_path = _reviewed_document_target(
        document,
        project,
    )
    if (
        target_strategy != action.get('target_strategy')
        or target_path != action.get('target_path')
    ):
        raise CommandError(
            f'La ruta revisada del documento {document.id} cambió desde el plan.'
        )

    previous_folder_ids = set(
        DocumentFolder.objects.values_list('id', flat=True)
    )
    effective_client = document.client_user or project.client
    if target_strategy == 'generated_path':
        cancelled = (
            document.commercial_status
            == Document.CommercialStatus.CANCELLED
        )
        target = ensure_generated_folder_path(
            COLLECTION_ACCOUNT,
            business_date=document.issue_date,
            project=project,
            client_user=effective_client,
            cancelled=cancelled,
            unissued=cancelled and not document.issue_date,
        )
    else:
        target = root

    inverse['changes'].append({
        'type': 'assigned_document_project',
        'document_id': document.id,
        'folder_id': document.folder_id,
        'project_id': document.project_id,
        'client_user_id': document.client_user_id,
        'created_folder_ids': sorted(
            set(DocumentFolder.objects.values_list('id', flat=True))
            - previous_folder_ids
        ),
    })
    document.folder = target
    document.project = project
    update_fields = ['folder', 'project', 'updated_at']
    if document.client_user_id is None:
        document.client_user = project.client
        update_fields.append('client_user')
    document.save(update_fields=update_fields)


@transaction.atomic
def apply_manifest(manifest):
    list(get_user_model().objects.select_for_update().values_list('id', flat=True))
    list(UserProfile.objects.select_for_update().values_list('id', flat=True))
    list(Project.objects.select_for_update().values_list('id', flat=True))
    list(DocumentState.objects.select_for_update().values_list('id', flat=True))
    list(DocumentType.objects.select_for_update().values_list('id', flat=True))
    list(DocumentFolder.objects.select_for_update().values_list('id', flat=True))
    list(Document.objects.select_for_update().values_list('id', flat=True))
    current_fingerprint = _sha256(_json_snapshot(database_snapshot()))
    if current_fingerprint != manifest.get('database_fingerprint'):
        raise CommandError(
            'Los proyectos, carpetas o documentos cambiaron desde el plan. '
            'Regenera y revisa un manifiesto nuevo.'
        )
    inverse = {'version': 4, 'generated_at': timezone.now().isoformat(), 'changes': []}

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
        if action['type'] != 'nest_project_root':
            continue
        _assert_no_conflicts(action)
        project = Project.objects.get(pk=action['project_id'])
        target_root = DocumentFolder.objects.filter(managed_project=project).first()
        if target_root is None:
            raise CommandError(
                f'El proyecto {project.id} no tiene una raíz gestionada aprobada.'
            )
        folder = DocumentFolder.objects.get(pk=action['folder_id'])
        if folder.parent_id is not None or folder.managed_project_id is not None:
            raise CommandError(
                f'La carpeta {folder.id} ya no es una raíz manual.'
            )
        if folder.id == target_root.id:
            raise CommandError(
                f'La carpeta {folder.id} ya es la raíz gestionada del proyecto.'
            )
        inverse['changes'].append({
            'type': 'nested_project_root',
            'folder_id': folder.id,
            'parent_id': folder.parent_id,
            'project_id': folder.project_id,
            'client_user_id': folder.client_user_id,
            'target_root_id': target_root.id,
        })
        _associate_tree(folder, project)
        folder.parent = target_root
        folder.save(update_fields=['parent', 'updated_at'])

    for action in approved:
        if action['type'] != 'assign_client_folder':
            continue
        _assert_no_conflicts(action)
        profile = UserProfile.objects.clients().select_related('user').get(
            pk=action['client_profile_id'],
        )
        folder = DocumentFolder.objects.get(pk=action['folder_id'])
        if folder.parent_id is not None or folder.managed_project_id is not None:
            raise CommandError(
                f'La carpeta {folder.id} ya no es una raíz manual.'
            )
        inverse['changes'].append({
            'type': 'assigned_client', 'folder_id': folder.id,
            'parent_id': folder.parent_id, 'project_id': folder.project_id,
            'client_user_id': folder.client_user_id,
        })
        _associate_client_tree(folder, profile)
    for action in approved:
        if action['type'] == 'file_document':
            _file_reviewed_document(action, inverse)
    for action in approved:
        if action['type'] == 'assign_document_project':
            _assign_reviewed_document_project(action, inverse)
    return inverse


class Command(BaseCommand):
    help = (
        'Genera una propuesta revisable o aplica un manifiesto aprobado para '
        'conciliar espacios de proyecto, cliente y carpetas sin asignar. '
        'Nunca aplica por nombre sin revisión.'
    )

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument('--plan', metavar='JSON_PATH')
        mode.add_argument('--apply-reviewed', metavar='JSON_PATH')
        parser.add_argument('--confirm', help='SHA-256 exacto del manifiesto revisado.')
        parser.add_argument('--inverse-out', help='Ruta del snapshot inverso generado.')
        parser.add_argument(
            '--backup-reference',
            help='Identificador o ruta del respaldo verificado antes de aplicar.',
        )
        parser.add_argument(
            '--nest-project-root', action='append', default=[],
            metavar='FOLDER_ID:PROJECT_ID',
            help='Raíz histórica que se anidará en un proyecto (repetible).',
        )
        parser.add_argument(
            '--assign-client-root', action='append', default=[],
            metavar='FOLDER_ID:PROFILE_ID',
            help='Asignación explícita carpeta raíz→cliente (repetible).',
        )
        parser.add_argument(
            '--assign-document-project', action='append', default=[],
            metavar='DOCUMENT_ID:PROJECT_ID',
            help='Asociación explícita documento sin carpeta→proyecto (repetible).',
        )

    def handle(self, *args, **options):
        if options['plan']:
            output = Path(options['plan']).expanduser().resolve()
            manifest = build_manifest(
                project_root_nestings=_parse_project_root_nestings(
                    options['nest_project_root'],
                ),
                client_root_assignments=_parse_client_root_assignments(
                    options['assign_client_root'],
                ),
                document_project_assignments=(
                    _parse_document_project_assignments(
                        options['assign_document_project'],
                    )
                ),
            )
            _write_json_atomic(output, manifest)
            report = output.with_suffix('.md')
            report.write_text(_markdown_report(manifest), encoding='utf-8')
            file_hash = hashlib.sha256(output.read_bytes()).hexdigest()
            self.stdout.write(f'Manifiesto: {output}')
            self.stdout.write(f'Reporte: {report}')
            self.stdout.write(f'SHA-256: {file_hash}')
            self.stdout.write('Dry-run: nada se escribió en la base de datos.')
            return

        if (
            options['nest_project_root']
            or options['assign_client_root']
            or options['assign_document_project']
        ):
            raise CommandError(
                'Las directivas de conciliación sólo se aceptan con --plan.'
            )
        if not options['backup_reference']:
            raise CommandError(
                '--backup-reference es obligatorio para aplicar un manifiesto.'
            )
        if not options['inverse_out']:
            raise CommandError(
                '--inverse-out es obligatorio para preparar la recuperación.'
            )

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
        inverse_path = Path(options['inverse_out']).expanduser().resolve()
        if inverse_path == reviewed:
            raise CommandError(
                'El snapshot inverso no puede reemplazar el manifiesto revisado.'
            )
        before = _json_snapshot(database_snapshot())
        prepared_inverse = {
            'version': 4,
            'status': 'prepared',
            'generated_at': timezone.now().isoformat(),
            'backup_reference': options['backup_reference'],
            'reviewed_manifest_sha256': actual_hash,
            'database_fingerprint': _sha256(before),
            'before': before,
            'changes': [],
        }
        _write_json_atomic(inverse_path, prepared_inverse)
        inverse = apply_manifest(manifest)
        inverse.update({
            'status': 'applied',
            'backup_reference': options['backup_reference'],
            'reviewed_manifest_sha256': actual_hash,
            'database_fingerprint': manifest['database_fingerprint'],
            'after_database_fingerprint': _sha256(
                _json_snapshot(database_snapshot())
            ),
            'before': before,
        })
        _write_json_atomic(inverse_path, inverse)
        self.stdout.write(self.style.SUCCESS(
            f'Manifiesto aplicado. Snapshot inverso: {inverse_path}'
        ))
