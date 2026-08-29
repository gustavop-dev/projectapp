"""The project-folder migration is review-first and drift-safe."""
import hashlib
import json

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts.models import Project, UserProfile
from content.management.commands.reconcile_project_folders import (
    build_manifest,
    database_snapshot,
)
from content.models import Document, DocumentFolder


pytestmark = pytest.mark.django_db


def make_project(email, name, *, first='', last='', company=''):
    user = get_user_model().objects.create_user(
        username=email,
        email=email,
        first_name=first,
        last_name=last,
    )
    UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
        company_name=company,
    )
    project = Project.objects.create(name=name, client=user)
    root = project.document_root_folder
    root.children.all().delete()
    root.delete()
    return project


def reviewed_file(path, manifest, approved_types=()):
    for action in manifest['actions']:
        action['decision'] = (
            'approve' if action['type'] in approved_types else 'skip'
        )
    path.write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reviewed_kore_adoption(tmp_path, *, include_document):
    project = make_project(
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
        build_manifest(),
        approved_types=('convert', 'nest_client_folder'),
    )
    return project, project_folder, client_folder, document, reviewed, digest


def test_manifest_proposes_current_conversion_and_client_nesting_rules():
    make_project('gm@example.com', 'G&M', company='G&M')
    make_project(
        'german@example.com', 'Kore Health',
        first='Germán', last='Franco',
    )
    gm = DocumentFolder.objects.create(name='G&M Project')
    kore = DocumentFolder.objects.create(name='Kore - Diseño')
    german = DocumentFolder.objects.create(name='Germán Franco')

    manifest = build_manifest()

    by_folder = {
        action.get('folder_id'): action for action in manifest['actions']
    }
    assert by_folder[gm.id]['type'] == 'convert'
    assert by_folder[kore.id]['type'] == 'convert'
    assert by_folder[german.id]['type'] == 'nest_client_folder'
    assert manifest['missing_expected_names'] == ['Proyegabs']


def test_plan_command_keeps_database_unchanged(tmp_path):
    """Falla si generar la propuesta modifica proyectos, carpetas o documentos."""
    make_project('vastago@example.com', 'Vastago')
    DocumentFolder.objects.create(name='Vastago Project')
    output = tmp_path / 'project-folders.json'
    before = database_snapshot()

    call_command('reconcile_project_folders', plan=str(output))

    assert database_snapshot() == before
    assert output.exists()
    assert output.with_suffix('.md').exists()


def test_apply_adopts_reviewed_folder_relationships(tmp_path):
    """Falla si la conversión aprobada no crea la jerarquía de proyecto."""
    project, project_folder, client_folder, _, reviewed, digest = (
        reviewed_kore_adoption(tmp_path, include_document=False)
    )

    call_command(
        'reconcile_project_folders',
        apply_reviewed=str(reviewed),
        confirm=digest,
    )

    project_folder.refresh_from_db()
    client_folder.refresh_from_db()
    assert project_folder.managed_project_id == project.id
    assert project_folder.name == 'Kore Health'
    assert client_folder.parent_id == project_folder.id
    assert reviewed.with_suffix('.inverse.json').exists()


def test_apply_preserves_document_location_and_content(tmp_path):
    """Falla si adoptar una carpeta mueve o altera el documento existente."""
    project, _, client_folder, document, reviewed, digest = reviewed_kore_adoption(
        tmp_path, include_document=True,
    )

    call_command(
        'reconcile_project_folders',
        apply_reviewed=str(reviewed),
        confirm=digest,
    )

    document.refresh_from_db()
    assert document.folder_id == client_folder.id
    assert document.title == 'Acta'
    assert document.content_json == {
        'meta': {'title': 'Acta'}, 'blocks': [{'type': 'text'}],
    }
    assert document.project_id == project.id
    assert document.client_user_id == project.client_id


def test_apply_rejects_incomplete_review(tmp_path):
    """Falla si una revisión incompleta deja una conversión parcial."""
    make_project('pending@example.com', 'Pending')
    manifest = build_manifest()
    reviewed = tmp_path / 'pending.json'
    reviewed.write_text(json.dumps(manifest), encoding='utf-8')
    digest = hashlib.sha256(reviewed.read_bytes()).hexdigest()
    before = database_snapshot()

    with pytest.raises(CommandError, match='revisión está incompleta'):
        call_command(
            'reconcile_project_folders',
            apply_reviewed=str(reviewed),
            confirm=digest,
        )
    assert database_snapshot() == before


def test_apply_rejects_database_drift(tmp_path):
    """Falla si el rechazo por drift deja cambios parciales en la jerarquía."""
    make_project('drift@example.com', 'Drift')
    folder = DocumentFolder.objects.create(name='Drift Project')
    manifest = build_manifest()
    reviewed = tmp_path / 'drift.json'
    digest = reviewed_file(reviewed, manifest)
    folder.name = 'Changed after review'
    folder.save(update_fields=['name', 'updated_at'])
    before = database_snapshot()

    with pytest.raises(CommandError, match='cambiaron desde el plan'):
        call_command(
            'reconcile_project_folders',
            apply_reviewed=str(reviewed),
            confirm=digest,
        )
    assert database_snapshot() == before


def test_apply_rejects_confirm_hash_mismatch_without_mutating_database(tmp_path):
    """Falla si un SHA de confirmación inválido alcanza a aplicar el manifiesto."""
    make_project('hash@example.com', 'Hash')
    DocumentFolder.objects.create(name='Hash Project')
    manifest = build_manifest()
    reviewed = tmp_path / 'hash.json'
    reviewed_file(reviewed, manifest, approved_types=('convert',))
    before = database_snapshot()

    with pytest.raises(CommandError, match='Confirmación inválida'):
        call_command(
            'reconcile_project_folders',
            apply_reviewed=str(reviewed),
            confirm='0' * 64,
        )

    assert database_snapshot() == before


def test_manifest_flags_a_second_project_root_instead_of_guessing():
    project = make_project('duplicate@example.com', 'Kore Health')
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
