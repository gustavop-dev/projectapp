"""Behavioral coverage for automatic project roots in Documents."""
import pytest

from accounts.models import Project, UserProfile
from content.models import DocumentFolder
from content.services.project_document_folder_service import (
    ProjectFolderReconciliationRequired,
    ensure_project_folder,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def client_profile(django_user_model):
    user = django_user_model.objects.create_user(
        username='folder-owner@example.com',
        email='folder-owner@example.com',
        password='pass12345',
    )
    return UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
    )


@pytest.fixture
def project(client_profile):
    return Project.objects.create(
        name='Kore Health',
        client=client_profile.user,
    )


def test_project_creation_builds_one_managed_root(project):
    root = DocumentFolder.objects.get(managed_project=project)

    assert root.name == 'Kore Health'
    assert root.parent_id is None
    assert root.project_id == project.id
    assert root.client_user_id == project.client_id
    assert root.folder_kind == 'project'


def test_disabled_project_creation_does_not_build_a_root(client_profile):
    project = Project.objects.create(
        name='PRUEBA',
        client=client_profile.user,
        document_manager_enabled=False,
    )

    assert not DocumentFolder.objects.filter(managed_project=project).exists()


def test_disabled_project_cannot_be_provisioned_implicitly(client_profile):
    project = Project.objects.create(
        name='PRUEBA',
        client=client_profile.user,
        document_manager_enabled=False,
    )

    with pytest.raises(ProjectFolderReconciliationRequired, match='no está habilitado'):
        ensure_project_folder(project)


def test_project_creation_builds_standard_children(project):
    """Falla si una raíz nueva deja de crear la estructura documental acordada."""
    root = project.document_root_folder

    assert list(root.children.values_list('name', flat=True)) == [
        'Cuentas de cobro',
        'Propuestas',
        'Entregables',
        'QA',
    ]
    assert not root.children.exclude(
        project=project,
        client_user=project.client,
    ).exists()
    children = {child.name: child for child in root.children.all()}
    assert children['Cuentas de cobro'].system_key == (
        f'generated:project:{project.id}:collection_account'
    )
    assert children['Propuestas'].system_key == (
        f'generated:project:{project.id}:commercial_proposal'
    )
    assert children['Entregables'].system_key is None
    assert children['QA'].system_key is None


def test_ensure_project_folder_is_idempotent(project):
    first = ensure_project_folder(project)
    second = ensure_project_folder(project)

    assert first.pk == second.pk
    assert DocumentFolder.objects.filter(managed_project=project).count() == 1
    assert first.children.count() == 4


def test_project_rename_synchronizes_root_without_changing_slug(project):
    root = project.document_root_folder
    original_slug = root.slug

    project.name = 'Kore Platform'
    project.save(update_fields=['name', 'updated_at'])

    root.refresh_from_db()
    assert root.name == 'Kore Platform'
    assert root.slug == original_slug


def test_updating_a_historical_project_never_recreates_a_missing_root(project):
    root = project.document_root_folder
    root.children.all().delete()
    root.delete()

    project.description = 'Edición ordinaria después de la migración de esquema'
    project.save(update_fields=['description', 'updated_at'])

    assert not DocumentFolder.objects.filter(managed_project=project).exists()


def test_enabling_a_historical_project_still_requires_reviewed_adoption(project):
    root = project.document_root_folder
    root.children.all().delete()
    root.delete()
    project.document_manager_enabled = False
    project.save(update_fields=['document_manager_enabled', 'updated_at'])

    project.document_manager_enabled = True
    project.save(update_fields=['document_manager_enabled', 'updated_at'])

    assert not DocumentFolder.objects.filter(managed_project=project).exists()


def test_project_client_change_synchronizes_its_folder_tree(
    project,
    django_user_model,
):
    user = django_user_model.objects.create_user(
        username='new-owner@example.com',
        email='new-owner@example.com',
        password='pass12345',
    )
    UserProfile.objects.create(user=user, role=UserProfile.ROLE_CLIENT)

    project.client = user
    project.save(update_fields=['client', 'updated_at'])

    root = DocumentFolder.objects.get(managed_project=project)
    assert root.client_user_id == user.id
    assert not root.children.exclude(client_user=user).exists()


def test_project_delete_preserves_root_as_manual(project):
    root_id = project.document_root_folder.id

    project.delete()

    root = DocumentFolder.objects.get(pk=root_id)
    assert root.managed_project_id is None
    assert root.project_id is None
    assert root.parent_id is None
    assert root.folder_kind == 'manual'
