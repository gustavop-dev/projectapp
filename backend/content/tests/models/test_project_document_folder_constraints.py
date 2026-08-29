"""Database invariants for roots owned by a Project lifecycle."""
import pytest
from accounts.models import Project
from django.db import IntegrityError, transaction

from content.models import DocumentFolder


pytestmark = pytest.mark.django_db


@pytest.fixture
def project_without_root(django_user_model):
    """Create a project through bulk SQL so its post-save root is not created."""
    client = django_user_model.objects.create_user(
        username='constraint-owner@example.com',
        email='constraint-owner@example.com',
        password='pass12345',
    )
    Project.objects.bulk_create([Project(name='Constraint project', client=client)])
    return Project.objects.get(name='Constraint project')


def test_managed_project_root_rejects_a_parent(project_without_root):
    """Falla si una subcarpeta puede convertirse en raíz automática."""
    parent = DocumentFolder.objects.create(name='Manual parent')

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            DocumentFolder.objects.create(
                name='Nested managed root',
                parent=parent,
                project=project_without_root,
                managed_project=project_without_root,
            )


def test_managed_project_root_rejects_another_project(project_without_root):
    """Falla si una raíz automática deja de coincidir con su proyecto."""
    other_project = Project(
        name='Other constraint project',
        client=project_without_root.client,
    )
    Project.objects.bulk_create([other_project])
    other_project.refresh_from_db()

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            DocumentFolder.objects.create(
                name='Mismatched managed root',
                project=other_project,
                managed_project=project_without_root,
            )


def test_managed_project_root_rejects_archiving(project_without_root):
    """Falla si una raíz automática puede entrar archivada a la base."""
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            DocumentFolder.objects.create(
                name='Archived managed root',
                project=project_without_root,
                managed_project=project_without_root,
                is_archived=True,
            )
