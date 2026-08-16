"""Tests del comando link_documents_from_folders (retroactivo carpeta→dueño)."""
from io import StringIO

import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model
from django.core.management import call_command

from content.models import Document, DocumentFolder

pytestmark = pytest.mark.django_db


def make_client(email, *, first='Ana', last='Pérez', company=''):
    user = get_user_model().objects.create_user(
        username=email, email=email, password='pass12345',
        first_name=first, last_name=last,
    )
    return UserProfile.objects.create(user=user, company_name=company)


def run_command(*args):
    out = StringIO()
    call_command('link_documents_from_folders', *args, stdout=out)
    return out.getvalue()


class TestLinkDocumentsFromFolders:
    def test_dry_run_writes_nothing(self):
        profile = make_client('kore@example.com', first='Kore')
        Project.objects.create(name='Vastago', client=profile.user)
        folder = DocumentFolder.objects.create(name='Vastago Proj')
        document = Document.objects.create(title='Doc', folder=folder)

        output = run_command()

        document.refresh_from_db()
        assert document.project is None
        assert document.client_user is None
        assert 'Dry-run' in output
        assert '[carpeta→proyecto]' in output

    def test_folder_matching_a_project_links_it_and_derives_the_owner(self):
        profile = make_client('deivis@example.com', first='Deivis', last='Ríos')
        project = Project.objects.create(name='Vastago', client=profile.user)
        folder = DocumentFolder.objects.create(name='Vastago Proj')
        document = Document.objects.create(title='Entregable', folder=folder)

        run_command('--apply')

        document.refresh_from_db()
        assert document.project == project
        assert document.client_user == profile.user
        assert 'Deivis' in document.client_name

    def test_folder_half_before_the_dash_matches_the_project(self):
        profile = make_client('kore@example.com', first='Kore', last='SAS')
        project = Project.objects.create(name='Kore', client=profile.user)
        folder = DocumentFolder.objects.create(name='Kore - Diseño')
        document = Document.objects.create(title='Mockups', folder=folder)

        run_command('--apply')

        document.refresh_from_db()
        assert document.project == project

    def test_folder_matching_a_unique_client_links_only_the_client(self):
        profile = make_client('carlos@example.com', first='Carlos', last='Ruiz')
        folder = DocumentFolder.objects.create(name='Carlos')
        document = Document.objects.create(title='Notas', folder=folder)

        run_command('--apply')

        document.refresh_from_db()
        assert document.client_user == profile.user
        assert document.project is None
        assert 'Carlos' in document.client_name

    def test_two_clients_with_the_same_name_stay_ambiguous(self):
        make_client('carlos1@example.com', first='Carlos', last='Ruiz')
        make_client('carlos2@example.com', first='Carlos', last='Gómez')
        folder = DocumentFolder.objects.create(name='Carlos')
        document = Document.objects.create(title='Notas', folder=folder)

        output = run_command('--apply')

        document.refresh_from_db()
        assert document.client_user is None
        assert '[ambigua]' in output

    def test_already_linked_documents_are_always_skipped(self):
        carlos = make_client('carlos@example.com', first='Carlos', last='Ruiz')
        other = make_client('otro@example.com', first='Otra', last='Dueña')
        folder = DocumentFolder.objects.create(name='Carlos')
        document = Document.objects.create(
            title='Ajeno', folder=folder, client_user=other.user,
        )

        run_command('--apply')

        document.refresh_from_db()
        assert document.client_user == other.user
        assert carlos.user != other.user

    def test_documents_with_project_inherit_its_owner(self):
        profile = make_client('kore@example.com', first='Kore', last='SAS')
        project = Project.objects.create(name='Kore', client=profile.user)
        document = Document.objects.create(title='Suelto', project=project)

        output = run_command('--apply')

        document.refresh_from_db()
        assert document.client_user == profile.user
        assert '[normalize]' in output

    def test_subfolders_inherit_the_nearest_ancestor_match(self):
        profile = make_client('kore@example.com', first='Kore', last='SAS')
        project = Project.objects.create(name='Kore', client=profile.user)
        parent = DocumentFolder.objects.create(name='Kore - Diseño')
        child = DocumentFolder.objects.create(name='Entregas', parent=parent)
        document = Document.objects.create(title='Entrega 1', folder=child)

        run_command('--apply')

        document.refresh_from_db()
        assert document.project == project
        assert document.client_user == profile.user

    def test_a_second_apply_run_reports_zero(self):
        profile = make_client('kore@example.com', first='Kore', last='SAS')
        Project.objects.create(name='Kore', client=profile.user)
        folder = DocumentFolder.objects.create(name='Kore - Diseño')
        Document.objects.create(title='Mockups', folder=folder)

        run_command('--apply')
        output = run_command('--apply')

        assert 'Aplicado: 0 documento(s)' in output
