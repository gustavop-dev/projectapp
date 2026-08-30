"""The document reconciliation is review-first, explicit and drift-safe."""
import hashlib
import json
from copy import deepcopy
from datetime import date
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts.models import Project, UserProfile
from content.management.commands.reconcile_project_folders import (
    MANIFEST_VERSION,
    build_manifest,
    database_snapshot,
)
from content.models import (
    Document,
    DocumentFolder,
    DocumentState,
    DocumentStateGroup,
)
from content.services.document_type_utils import get_collection_account_document_type


pytestmark = pytest.mark.django_db


def make_project(email, name, *, first='', last='', company=''):
    user = get_user_model().objects.create_user(
        username=email,
        email=email,
        first_name=first,
        last_name=last,
    )
    profile = UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
        company_name=company,
    )
    project = Project.objects.create(name=name, client=user)
    root = project.document_root_folder
    root.children.all().delete()
    root.delete()
    return project, profile


def reviewed_file(path, manifest, approved_types=()):
    for action in manifest['actions']:
        action['decision'] = (
            'approve' if action['type'] in approved_types else 'skip'
        )
    path.write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_reviewed(path, digest, tmp_path):
    inverse = tmp_path / f'{path.stem}.inverse.json'
    call_command(
        'reconcile_project_folders',
        apply_reviewed=str(path),
        confirm=digest,
        backup_reference='backup:test-verified',
        inverse_out=str(inverse),
    )
    return inverse


def reviewed_kore_adoption(tmp_path, *, include_document):
    project, profile = make_project(
        'german-apply@example.com', 'Kore Health',
        first='Germán', last='Franco',
    )
    project_folder = DocumentFolder.objects.create(name='Kore - Diseño')
    client_folder = DocumentFolder.objects.create(name='Germán Franco')
    document = None
    if include_document:
        document = Document.objects.create(
            title='Acta',
            folder=client_folder,
            content_json={
                'meta': {'title': 'Acta'},
                'blocks': [{'type': 'text'}],
            },
        )
    reviewed = tmp_path / 'reviewed.json'
    digest = reviewed_file(
        reviewed,
        build_manifest(project_root_nestings={client_folder.id: project.id}),
        approved_types=('convert', 'nest_project_root'),
    )
    return (
        project, profile, project_folder, client_folder, document,
        reviewed, digest,
    )


def make_folderless_account(project):
    return Document.objects.create(
        title='Cuenta histórica de Mimittos',
        document_type=get_collection_account_document_type(),
        commercial_status=Document.CommercialStatus.ISSUED,
        issue_date=date(2026, 8, 14),
        project=project,
        client_user=project.client,
    )


def make_unassigned_document(*, client_user=None, title='Documento histórico'):
    return Document.objects.create(
        title=title,
        client_user=client_user,
        client_name='Nombre histórico preservado',
        content_markdown='# Contenido histórico',
    )


def test_manifest_proposes_project_root_nesting():
    make_project('gm@example.com', 'G&M', company='G&M')
    kore_project, _german_profile = make_project(
        'german@example.com', 'Kore Health',
        first='Germán', last='Franco',
    )
    gm = DocumentFolder.objects.create(name='G&M Project')
    kore = DocumentFolder.objects.create(name='Kore - Diseño')
    german = DocumentFolder.objects.create(name='Germán Franco')

    manifest = build_manifest(
        project_root_nestings={german.id: kore_project.id},
    )

    by_folder = {
        action.get('folder_id'): action for action in manifest['actions']
    }
    assert by_folder[gm.id]['type'] == 'convert'
    assert by_folder[kore.id]['type'] == 'convert'
    assert by_folder[german.id]['type'] == 'nest_project_root'
    assert by_folder[german.id]['project_id'] == kore_project.id
    assert by_folder[german.id]['target_root_action_id'] == by_folder[kore.id]['id']
    assert manifest['missing_expected_names'] == ['Proyegabs']


def test_plan_command_keeps_database_unchanged(tmp_path):
    """Falla si generar un plan modifica las filas que debe revisar."""
    make_project('prueba@example.com', 'PRUEBA')
    output = tmp_path / 'document-reconciliation.json'
    before = database_snapshot()

    call_command('reconcile_project_folders', plan=str(output))

    assert database_snapshot() == before


def test_plan_command_records_project_root_nesting_directive(tmp_path):
    """Falla si el plan pierde una instrucción explícita de anidamiento."""
    nested_project, _nested_profile = make_project(
        'carlos@example.com', 'Otro proyecto', first='Carlos',
    )
    nested_root = DocumentFolder.objects.create(name='Carlos')
    output = tmp_path / 'document-reconciliation.json'

    call_command(
        'reconcile_project_folders',
        plan=str(output),
        nest_project_root=[f'{nested_root.id}:{nested_project.id}'],
    )

    manifest = json.loads(output.read_text(encoding='utf-8'))
    assert manifest['planning_directives']['project_root_nestings'] == [{
        'folder_id': nested_root.id,
        'project_id': nested_project.id,
    }]


def test_plan_command_records_client_root_assignment_directive(tmp_path):
    """Falla si el plan pierde una asignación explícita de cliente."""
    _client_project, client_profile = make_project(
        'gustavo@example.com', 'Proyecto sin carpeta', first='Gustavo',
    )
    client_root = DocumentFolder.objects.create(name='Gustavo')
    output = tmp_path / 'document-reconciliation.json'

    call_command(
        'reconcile_project_folders',
        plan=str(output),
        assign_client_root=[f'{client_root.id}:{client_profile.id}'],
    )

    manifest = json.loads(output.read_text(encoding='utf-8'))
    assert manifest['planning_directives']['client_root_assignments'] == [{
        'folder_id': client_root.id,
        'client_profile_id': client_profile.id,
    }]


def test_plan_records_document_project_assignment_to_managed_root(tmp_path):
    project, _profile = make_project('vastago@example.com', 'Vástago')
    document = make_unassigned_document()
    output = tmp_path / 'document-reconciliation.json'

    call_command(
        'reconcile_project_folders',
        plan=str(output),
        assign_document_project=[f'{document.id}:{project.id}'],
    )

    manifest = json.loads(output.read_text(encoding='utf-8'))
    action = next(
        row for row in manifest['actions']
        if row.get('document_id') == document.id
    )
    assert manifest['version'] == 5
    assert manifest['planning_directives']['document_project_assignments'] == [{
        'document_id': document.id,
        'project_id': project.id,
    }]
    assert action['type'] == 'assign_document_project'
    assert action['target_strategy'] == 'project_root'
    assert action['target_path'] == 'Proyectos / Vástago'


def test_plan_rejects_conflicting_document_project_directives(tmp_path):
    first, _first_profile = make_project('first@example.com', 'Primero')
    second, _second_profile = make_project('second@example.com', 'Segundo')
    document = make_unassigned_document()

    with pytest.raises(CommandError, match='dos proyectos distintos'):
        call_command(
            'reconcile_project_folders',
            plan=str(tmp_path / 'conflicting.json'),
            assign_document_project=[
                f'{document.id}:{first.id}',
                f'{document.id}:{second.id}',
            ],
        )


def test_apply_rejects_document_assignment_directive(tmp_path):
    project, _profile = make_project('plan-only@example.com', 'Plan only')
    document = make_unassigned_document()

    with pytest.raises(CommandError, match='sólo se aceptan con --plan'):
        call_command(
            'reconcile_project_folders',
            apply_reviewed=str(tmp_path / 'missing.json'),
            assign_document_project=[f'{document.id}:{project.id}'],
        )


def test_plan_uses_canonical_path_for_assigned_collection_account():
    project, _profile = make_project('tenndalux@example.com', 'Tenndalux')
    document = Document.objects.create(
        title='Cuenta histórica',
        document_type=get_collection_account_document_type(),
        commercial_status=Document.CommercialStatus.ISSUED,
        issue_date=date(2026, 8, 14),
        client_user=project.client,
    )

    manifest = build_manifest(
        document_project_assignments={document.id: project.id},
    )

    action = next(
        row for row in manifest['actions']
        if row.get('document_id') == document.id
    )
    assert action['target_strategy'] == 'generated_path'
    assert action['target_path'] == (
        'Proyectos / Tenndalux / Cuentas de cobro / 2026 / 08 - Agosto'
    )


def test_plan_rejects_unknown_document_assignment():
    project, _profile = make_project('known-project@example.com', 'Conocido')

    with pytest.raises(CommandError, match='No existen los documentos'):
        build_manifest(document_project_assignments={999999: project.id})


def test_plan_rejects_unknown_project_assignment():
    document = make_unassigned_document()

    with pytest.raises(CommandError, match='No existen los proyectos'):
        build_manifest(document_project_assignments={document.id: 999999})


def test_plan_rejects_document_that_is_already_filed():
    project, _profile = make_project('filed@example.com', 'Filed')
    folder = DocumentFolder.objects.create(name='Ubicación manual')
    document = make_unassigned_document()
    document.folder = folder
    document.save(update_fields=['folder', 'updated_at'])

    with pytest.raises(CommandError, match='documentos sin carpeta'):
        build_manifest(document_project_assignments={document.id: project.id})


def test_plan_rejects_document_that_already_has_project():
    project, _profile = make_project('linked@example.com', 'Linked')
    document = make_unassigned_document(client_user=project.client)
    document.project = project
    document.save(update_fields=['project', 'updated_at'])

    with pytest.raises(CommandError, match='documentos sin proyecto'):
        build_manifest(document_project_assignments={document.id: project.id})


def test_plan_rejects_document_from_another_client():
    project, _profile = make_project('target@example.com', 'Target')
    other, _other_profile = make_project('other@example.com', 'Other')
    document = make_unassigned_document(client_user=other.client)

    with pytest.raises(CommandError, match='pertenecen a otro cliente'):
        build_manifest(document_project_assignments={document.id: project.id})


def test_plan_command_proposes_prueba_root(tmp_path):
    """Falla si PRUEBA queda fuera del catálogo conciliable."""
    prueba, _profile = make_project('prueba@example.com', 'PRUEBA')
    output = tmp_path / 'document-reconciliation.json'

    call_command('reconcile_project_folders', plan=str(output))

    manifest = json.loads(output.read_text(encoding='utf-8'))
    assert any(
        action['type'] == 'create' and action['project_id'] == prueba.id
        for action in manifest['actions']
    )


def test_plan_command_writes_a_markdown_review_sidecar(tmp_path):
    """Falla si el plan deja de entregar el reporte legible de revisión."""
    make_project('prueba@example.com', 'PRUEBA')
    output = tmp_path / 'document-reconciliation.json'

    call_command('reconcile_project_folders', plan=str(output))

    report = output.with_suffix('.md')
    assert report.read_text(encoding='utf-8').startswith(
        '# Propuesta de conciliación del Gestor Documental\n'
    )


def test_plan_rejects_a_source_that_changes_while_it_is_generated():
    make_project('moving-plan@example.com', 'Moving plan')
    initial = database_snapshot()
    changed = deepcopy(initial)
    changed['projects'][0]['name'] = 'Changed during planning'

    with patch(
        'content.management.commands.reconcile_project_folders.database_snapshot',
        side_effect=[initial, changed],
    ):
        with pytest.raises(CommandError, match='mientras se generaba el plan'):
            build_manifest()


def test_manifest_groups_suspended_candle_as_archived():
    candle, _ = make_project('candle@example.com', 'Candle')
    suspended = DocumentState.objects.get(
        catalog=DocumentStateGroup.Catalog.PROJECTS,
        operational_effect=DocumentState.OperationalEffect.SUSPENDED,
    )
    candle.current_state = suspended
    candle.status = Project.STATUS_SUSPENDED
    candle.save(update_fields=['current_state', 'status', 'updated_at'])

    manifest = build_manifest()

    candle_root = next(
        row for row in manifest['actions']
        if row['type'] == 'create' and row['project_id'] == candle.id
    )
    assert candle_root['catalog_bucket'] == 'archived'


def test_manifest_proposes_a_reviewed_path_for_a_folderless_project_account():
    project, _ = make_project('mimittos@example.com', 'Mimittos')
    document = make_folderless_account(project)

    manifest = build_manifest()

    action = next(
        row for row in manifest['actions']
        if row.get('document_id') == document.id
    )
    assert manifest['version'] == MANIFEST_VERSION
    assert action['type'] == 'file_document'
    assert action['decision'] == 'pending'
    assert action['target_path'] == (
        'Proyectos / Mimittos / Cuentas de cobro / 2026 / 08 - Agosto'
    )


def test_apply_files_only_the_reviewed_project_document(tmp_path):
    project, _ = make_project('mimittos-apply@example.com', 'Mimittos')
    document = make_folderless_account(project)
    original_title = document.title
    reviewed = tmp_path / 'mimittos-reviewed.json'
    digest = reviewed_file(
        reviewed,
        build_manifest(),
        approved_types=('create', 'file_document'),
    )

    inverse_path = apply_reviewed(reviewed, digest, tmp_path)

    document.refresh_from_db()
    assert document.title == original_title
    assert document.project_id == project.id
    assert [
        *(folder.name for folder in document.folder.get_ancestors()),
        document.folder.name,
    ] == ['Mimittos', 'Cuentas de cobro', '2026', '08 - Agosto']
    inverse = json.loads(inverse_path.read_text(encoding='utf-8'))
    assert inverse['status'] == 'applied'
    assert inverse['backup_reference'] == 'backup:test-verified'
    assert inverse['before']
    filed = next(
        row for row in inverse['changes'] if row['type'] == 'filed_document'
    )
    assert filed['document_id'] == document.id
    assert filed['folder_id'] is None


def test_apply_assigns_plain_document_to_project_root_and_records_inverse(
    tmp_path,
):
    project, _profile = make_project('vastago-apply@example.com', 'Vástago')
    document = make_unassigned_document()
    original_client_name = document.client_name
    reviewed = tmp_path / 'vastago-reviewed.json'
    digest = reviewed_file(
        reviewed,
        build_manifest(
            document_project_assignments={document.id: project.id},
        ),
        approved_types=('create', 'assign_document_project'),
    )

    inverse_path = apply_reviewed(reviewed, digest, tmp_path)

    document.refresh_from_db()
    root = DocumentFolder.objects.get(managed_project=project)
    assert document.folder_id == root.id
    assert document.project_id == project.id
    assert document.client_user_id == project.client_id
    assert document.client_name == original_client_name
    inverse = json.loads(inverse_path.read_text(encoding='utf-8'))
    assignment = next(
        row for row in inverse['changes']
        if row['type'] == 'assigned_document_project'
    )
    assert assignment == {
        'type': 'assigned_document_project',
        'document_id': document.id,
        'folder_id': None,
        'project_id': None,
        'client_user_id': None,
        'created_folder_ids': [],
    }


def test_apply_assigns_collection_account_to_generated_project_path(tmp_path):
    project, _profile = make_project('gm-apply@example.com', 'G&M')
    document = Document.objects.create(
        title='Cuenta sin asociación',
        document_type=get_collection_account_document_type(),
        commercial_status=Document.CommercialStatus.ISSUED,
        issue_date=date(2026, 8, 2),
    )
    reviewed = tmp_path / 'gm-reviewed.json'
    digest = reviewed_file(
        reviewed,
        build_manifest(
            document_project_assignments={document.id: project.id},
        ),
        approved_types=('create', 'assign_document_project'),
    )

    inverse_path = apply_reviewed(reviewed, digest, tmp_path)

    document.refresh_from_db()
    assert document.project_id == project.id
    assert document.client_user_id == project.client_id
    assert [
        *(folder.name for folder in document.folder.get_ancestors()),
        document.folder.name,
    ] == ['G&M', 'Cuentas de cobro', '2026', '08 - Agosto']
    inverse = json.loads(inverse_path.read_text(encoding='utf-8'))
    assignment = next(
        row for row in inverse['changes']
        if row['type'] == 'assigned_document_project'
    )
    assert assignment['created_folder_ids']


def test_apply_requires_approved_root_for_document_assignment(tmp_path):
    project, _profile = make_project('root-required@example.com', 'Sin raíz')
    document = make_unassigned_document()
    reviewed = tmp_path / 'root-required.json'
    digest = reviewed_file(
        reviewed,
        build_manifest(
            document_project_assignments={document.id: project.id},
        ),
        approved_types=('assign_document_project',),
    )

    with pytest.raises(CommandError, match='requiere aprobar su raíz'):
        apply_reviewed(reviewed, digest, tmp_path)

    document.refresh_from_db()
    assert document.project_id is None


def test_manifest_flags_a_project_document_inside_an_unrelated_tree():
    project, _ = make_project('outside@example.com', 'Outside')
    folder = DocumentFolder.objects.create(name='Clasificación manual')
    document = Document.objects.create(
        title='Ubicación elegida por operador',
        project=project,
        client_user=project.client,
        folder=folder,
    )

    manifest = build_manifest()

    action = next(
        row for row in manifest['actions']
        if row.get('document_id') == document.id
    )
    assert action['type'] == 'document_conflict'
    assert 'no se moverá por inferencia' in action['reason']


def test_apply_nests_legacy_root_under_adopted_project_root(tmp_path):
    (
        project, profile, project_folder, client_folder, _document,
        reviewed, digest,
    ) = reviewed_kore_adoption(tmp_path, include_document=False)

    inverse = apply_reviewed(reviewed, digest, tmp_path)

    project_folder.refresh_from_db()
    client_folder.refresh_from_db()
    assert project_folder.managed_project_id == project.id
    assert project_folder.name == 'Kore Health'
    assert client_folder.parent_id == project_folder.id
    assert client_folder.project_id == project.id
    assert client_folder.client_user_id == profile.user_id
    assert inverse.exists()


def test_apply_preserves_client_document_location_and_content(tmp_path):
    (
        _project, profile, _project_folder, client_folder, document,
        reviewed, digest,
    ) = reviewed_kore_adoption(tmp_path, include_document=True)

    apply_reviewed(reviewed, digest, tmp_path)

    document.refresh_from_db()
    assert document.folder_id == client_folder.id
    assert document.title == 'Acta'
    assert document.content_json == {
        'meta': {'title': 'Acta'}, 'blocks': [{'type': 'text'}],
    }
    assert document.project_id == _project.id
    assert document.client_user_id == profile.user_id


def test_apply_rejects_incomplete_review(tmp_path):
    make_project('pending@example.com', 'Pending')
    reviewed = tmp_path / 'pending.json'
    reviewed.write_text(json.dumps(build_manifest()), encoding='utf-8')
    digest = hashlib.sha256(reviewed.read_bytes()).hexdigest()
    before = database_snapshot()

    with pytest.raises(CommandError, match='revisión está incompleta'):
        call_command(
            'reconcile_project_folders',
            apply_reviewed=str(reviewed),
            confirm=digest,
            backup_reference='backup:test',
            inverse_out=str(tmp_path / 'pending.inverse.json'),
        )

    assert database_snapshot() == before


def test_apply_rejects_folder_and_client_drift(tmp_path):
    _project, profile = make_project('drift@example.com', 'Drift')
    folder = DocumentFolder.objects.create(name='Drift Project')
    manifest = build_manifest()
    reviewed = tmp_path / 'drift.json'
    digest = reviewed_file(reviewed, manifest)
    folder.name = 'Changed after review'
    folder.save(update_fields=['name', 'updated_at'])
    profile.company_name = 'Changed client identity'
    profile.save(update_fields=['company_name', 'updated_at'])
    before = database_snapshot()

    with pytest.raises(CommandError, match='cambiaron desde el plan'):
        apply_reviewed(reviewed, digest, tmp_path)

    assert database_snapshot() == before


def test_apply_requires_a_verified_backup_reference(tmp_path):
    make_project('backup@example.com', 'Backup')
    reviewed = tmp_path / 'backup.json'
    digest = reviewed_file(reviewed, build_manifest())

    with pytest.raises(CommandError, match='backup-reference'):
        call_command(
            'reconcile_project_folders',
            apply_reviewed=str(reviewed),
            confirm=digest,
            inverse_out=str(tmp_path / 'backup.inverse.json'),
        )


def test_apply_prepares_the_full_inverse_before_entering_the_transaction(
    tmp_path,
):
    make_project('prepared@example.com', 'Prepared')
    reviewed = tmp_path / 'prepared.json'
    digest = reviewed_file(reviewed, build_manifest())
    inverse = tmp_path / 'prepared.inverse.json'

    with patch(
        'content.management.commands.reconcile_project_folders.apply_manifest',
        side_effect=CommandError('simulated apply failure'),
    ), pytest.raises(CommandError, match='simulated apply failure'):
        call_command(
            'reconcile_project_folders',
            apply_reviewed=str(reviewed),
            confirm=digest,
            backup_reference='backup:verified',
            inverse_out=str(inverse),
        )

    artifact = json.loads(inverse.read_text(encoding='utf-8'))
    expected = json.loads(
        json.dumps(database_snapshot(), default=lambda value: value.isoformat())
    )
    assert artifact['status'] == 'prepared'
    assert artifact['backup_reference'] == 'backup:verified'
    assert artifact['before'] == expected


def test_apply_rejects_confirm_hash_mismatch_without_mutating_database(tmp_path):
    make_project('hash@example.com', 'Hash')
    DocumentFolder.objects.create(name='Hash Project')
    reviewed = tmp_path / 'hash.json'
    reviewed_file(reviewed, build_manifest(), approved_types=('convert',))
    before = database_snapshot()

    with pytest.raises(CommandError, match='Confirmación inválida'):
        call_command(
            'reconcile_project_folders',
            apply_reviewed=str(reviewed),
            confirm='0' * 64,
            backup_reference='backup:test',
            inverse_out=str(tmp_path / 'hash.inverse.json'),
        )

    assert database_snapshot() == before


def test_manifest_flags_a_second_project_root_instead_of_guessing():
    project, _ = make_project('duplicate@example.com', 'Kore Health')
    managed_root = DocumentFolder.objects.create(
        name=project.name,
        project=project,
        client_user=project.client,
        managed_project=project,
    )
    legacy = DocumentFolder.objects.create(name='Kore Project')

    manifest = build_manifest()

    action = next(
        row for row in manifest['actions'] if row.get('folder_id') == legacy.id
    )
    assert action['type'] == 'conflict'
    assert str(managed_root.id) in action['reason']
