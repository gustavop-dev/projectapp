"""The Projects module listing: the panel face of ``accounts.Project``.

Covers the scope selector (active hides archived by default, an invalid
value answers 400 because the param selects data), the accounting counts
each row carries, the client spoken in UserProfile terms, and the header
meta the module's stat cards read — including how many visible clients
still have no project registered.
"""
from decimal import Decimal

import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model
from django.utils import timezone

from content.models import HostingRecord, IncomeRecord

User = get_user_model()
pytestmark = pytest.mark.django_db

LIST_URL = '/api/projects/'


def make_client(email, *, first='Ana', last='Pérez', company=''):
    user = User.objects.create_user(
        username=email, email=email, password='pass12345',
        first_name=first, last_name=last,
    )
    return UserProfile.objects.create(user=user, company_name=company)


def make_project(profile, name, *, status=Project.STATUS_ACTIVE):
    return Project.objects.create(name=name, client=profile.user, status=status)


def make_income(**overrides):
    fields = {
        'concept': 'Desarrollo módulo de reportes',
        'kind': IncomeRecord.Kind.EXPECTED,
        'period_date': '2026-08-01',
        'total_amount': Decimal('1000000.00'),
        'gustavo_amount': Decimal('500000.00'),
        'carlos_amount': Decimal('500000.00'),
    }
    fields.update(overrides)
    return IncomeRecord.objects.create(**fields)


def make_hosting(profile, project, *, name='Cliente - Marca'):
    return HostingRecord.objects.create(
        client=profile,
        project=project,
        client_name=name,
        monthly_value=Decimal('120000.00'),
    )


def rows_by_name(response):
    return {row['name']: row for row in response.data['results']}


class TestListPanelProjects:
    def test_anonymous_is_rejected(self, api_client):
        # 401, not 403: the global JWT authenticator advertises a challenge.
        assert api_client.get(LIST_URL).status_code == 401

    def test_a_staff_admin_can_list_without_being_superuser(self, admin_client):
        owner = make_client('deivis@example.com')
        make_project(owner, 'Vastago')

        response = admin_client.get(LIST_URL)

        assert response.status_code == 200
        assert [row['name'] for row in response.data['results']] == ['Vastago']

    def test_default_scope_hides_archived_but_keeps_paused_and_completed(
        self, admin_client,
    ):
        owner = make_client('deivis@example.com')
        make_project(owner, 'Activo')
        make_project(owner, 'Pausado', status=Project.STATUS_PAUSED)
        make_project(owner, 'Completado', status=Project.STATUS_COMPLETED)
        make_project(owner, 'Viejo', status=Project.STATUS_ARCHIVED)

        response = admin_client.get(LIST_URL)

        names = [row['name'] for row in response.data['results']]
        assert names == ['Activo', 'Completado', 'Pausado']

    def test_scope_archived_returns_only_archived(self, admin_client):
        owner = make_client('deivis@example.com')
        make_project(owner, 'Activo')
        make_project(owner, 'Viejo', status=Project.STATUS_ARCHIVED)

        response = admin_client.get(LIST_URL, {'scope': 'archived'})

        names = [row['name'] for row in response.data['results']]
        assert names == ['Viejo']

    def test_scope_all_mixes_both_states(self, admin_client):
        owner = make_client('deivis@example.com')
        make_project(owner, 'Activo')
        make_project(owner, 'Viejo', status=Project.STATUS_ARCHIVED)

        response = admin_client.get(LIST_URL, {'scope': 'all'})

        names = [row['name'] for row in response.data['results']]
        assert names == ['Activo', 'Viejo']

    def test_an_invalid_scope_answers_400(self, admin_client):
        response = admin_client.get(LIST_URL, {'scope': 'trash'})

        assert response.status_code == 400
        assert response.data['code'] == 'invalid_scope'

    def test_rows_carry_their_accounting_counts(self, admin_client):
        owner = make_client('deivis@example.com')
        linked = make_project(owner, 'Con registros')
        bare = make_project(owner, 'Sin registros')
        make_hosting(owner, linked)
        make_hosting(owner, linked, name='Cliente - Marca 2')
        make_income(client=owner, project=linked)

        response = admin_client.get(LIST_URL)

        rows = rows_by_name(response)
        assert rows['Con registros']['hostings_count'] == 2
        assert rows['Con registros']['incomes_count'] == 1
        assert rows['Sin registros']['hostings_count'] == 0
        assert rows['Sin registros']['incomes_count'] == 0

    def test_the_client_travels_as_profile_id_and_display_name(
        self, admin_client,
    ):
        owner = make_client(
            'wilson@example.com', first='Wilson', last='García',
            company='Gimnasio W',
        )
        make_project(owner, 'Gimnasio')

        response = admin_client.get(LIST_URL)

        client = response.data['results'][0]['client']
        assert client == {
            'profile_id': owner.pk,
            'name': 'Wilson García',
            'company': 'Gimnasio W',
        }

    def test_meta_counts_clients_without_projects(self, admin_client):
        covered = make_client('deivis@example.com')
        make_project(covered, 'Vastago')
        make_client('wilson@example.com', first='Wilson')
        gone = make_client('viejo@example.com', first='Viejo')
        gone.deactivated_at = timezone.now()
        gone.save(update_fields=['deactivated_at'])

        response = admin_client.get(LIST_URL)

        meta = response.data['meta']
        assert meta['clients_without_projects'] == 1
        assert meta['total'] == 1
        assert meta['active'] == 1
        assert meta['archived'] == 0


CREATE_URL = '/api/projects/create/'


class TestCreatePanelProject:
    def test_the_minimal_payload_creates_an_active_project(self, admin_client):
        owner = make_client('deivis@example.com', first='Deivis', last='Ríos')

        response = admin_client.post(CREATE_URL, {
            'name': 'Vastago',
            'client_profile_id': owner.pk,
        }, format='json')

        assert response.status_code == 201, response.data
        assert response.data['name'] == 'Vastago'
        assert response.data['status'] == Project.STATUS_ACTIVE
        assert response.data['description'] == ''
        assert response.data['hostings_count'] == 0
        assert response.data['incomes_count'] == 0
        assert response.data['client']['profile_id'] == owner.pk
        project = Project.objects.get(pk=response.data['id'])
        assert project.client_id == owner.user_id

    def test_name_is_required(self, admin_client):
        owner = make_client('deivis@example.com')

        response = admin_client.post(CREATE_URL, {
            'client_profile_id': owner.pk,
        }, format='json')

        assert response.status_code == 400
        assert 'name' in response.data

    def test_the_client_is_required(self, admin_client):
        response = admin_client.post(CREATE_URL, {
            'name': 'Vastago',
        }, format='json')

        assert response.status_code == 400
        assert 'client_profile_id' in response.data

    def test_a_non_client_profile_is_rejected(self, admin_client):
        admin_profile = make_client('otroadmin@example.com')
        admin_profile.role = 'admin'
        admin_profile.save(update_fields=['role'])

        response = admin_client.post(CREATE_URL, {
            'name': 'Vastago',
            'client_profile_id': admin_profile.pk,
        }, format='json')

        assert response.status_code == 400
        assert 'client_profile_id' in response.data

    def test_a_duplicate_name_for_the_same_client_still_creates(
        self, admin_client,
    ):
        # The duplicate warning is client-side and never blocks: two rows
        # with the same name are a signal, not an error.
        owner = make_client('deivis@example.com')
        make_project(owner, 'Vastago')

        response = admin_client.post(CREATE_URL, {
            'name': 'Vastago',
            'client_profile_id': owner.pk,
        }, format='json')

        assert response.status_code == 201
        assert Project.objects.filter(name='Vastago').count() == 2

    def test_a_project_cannot_be_born_archived(self, admin_client):
        owner = make_client('deivis@example.com')

        response = admin_client.post(CREATE_URL, {
            'name': 'Vastago',
            'client_profile_id': owner.pk,
            'status': Project.STATUS_ARCHIVED,
        }, format='json')

        assert response.status_code == 400
        assert 'status' in response.data


class TestUpdatePanelProject:
    def test_name_description_and_status_can_change(self, admin_client):
        owner = make_client('deivis@example.com')
        project = make_project(owner, 'Vastago')

        response = admin_client.patch(
            f'/api/projects/{project.pk}/update/',
            {
                'name': 'Vástago App',
                'description': 'App de gestión',
                'status': Project.STATUS_PAUSED,
            },
            format='json',
        )

        assert response.status_code == 200, response.data
        project.refresh_from_db()
        assert project.name == 'Vástago App'
        assert project.description == 'App de gestión'
        assert project.status == Project.STATUS_PAUSED

    def test_the_client_is_immutable_from_the_panel(self, admin_client):
        owner = make_client('deivis@example.com')
        other = make_client('wilson@example.com', first='Wilson')
        project = make_project(owner, 'Vastago')

        response = admin_client.patch(
            f'/api/projects/{project.pk}/update/',
            {'client_profile_id': other.pk},
            format='json',
        )

        assert response.status_code == 400
        assert response.data['code'] == 'client_immutable'
        project.refresh_from_db()
        assert project.client_id == owner.user_id

    def test_an_archived_project_is_out_of_circulation(self, admin_client):
        owner = make_client('deivis@example.com')
        project = make_project(owner, 'Viejo', status=Project.STATUS_ARCHIVED)

        response = admin_client.patch(
            f'/api/projects/{project.pk}/update/',
            {'name': 'Renombrado'},
            format='json',
        )

        assert response.status_code == 400
        assert response.data['code'] == 'project_archived'

    def test_update_cannot_jump_to_archived(self, admin_client):
        # The dedicated archive endpoint owns that transition.
        owner = make_client('deivis@example.com')
        project = make_project(owner, 'Vastago')

        response = admin_client.patch(
            f'/api/projects/{project.pk}/update/',
            {'status': Project.STATUS_ARCHIVED},
            format='json',
        )

        assert response.status_code == 400
        assert 'status' in response.data


class TestArchivePanelProject:
    def test_archive_then_unarchive_roundtrip(self, admin_client):
        owner = make_client('deivis@example.com')
        project = make_project(owner, 'Vastago')

        archived = admin_client.patch(f'/api/projects/{project.pk}/archive/')
        assert archived.status_code == 200
        assert archived.data['status'] == Project.STATUS_ARCHIVED

        restored = admin_client.patch(f'/api/projects/{project.pk}/unarchive/')
        assert restored.status_code == 200
        assert restored.data['status'] == Project.STATUS_ACTIVE

    def test_archiving_twice_answers_400(self, admin_client):
        owner = make_client('deivis@example.com')
        project = make_project(owner, 'Viejo', status=Project.STATUS_ARCHIVED)

        response = admin_client.patch(f'/api/projects/{project.pk}/archive/')

        assert response.status_code == 400
        assert response.data['code'] == 'already_archived'

    def test_unarchiving_a_non_archived_project_answers_400(self, admin_client):
        owner = make_client('deivis@example.com')
        project = make_project(owner, 'Vastago')

        response = admin_client.patch(f'/api/projects/{project.pk}/unarchive/')

        assert response.status_code == 400
        assert response.data['code'] == 'not_archived'
