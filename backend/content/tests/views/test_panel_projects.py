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

    def test_default_scope_hides_archived_but_keeps_suspended_and_completed(
        self, admin_client,
    ):
        owner = make_client('deivis@example.com')
        make_project(owner, 'Activo')
        make_project(owner, 'Suspendido', status=Project.STATUS_SUSPENDED)
        make_project(owner, 'Completado', status=Project.STATUS_COMPLETED)
        make_project(owner, 'Viejo', status=Project.STATUS_ARCHIVED)

        response = admin_client.get(LIST_URL)

        names = [row['name'] for row in response.data['results']]
        assert names == ['Activo', 'Completado', 'Suspendido']

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
    def test_the_minimal_payload_creates_a_development_project(self, admin_client):
        owner = make_client('deivis@example.com', first='Deivis', last='Ríos')

        response = admin_client.post(CREATE_URL, {
            'name': 'Vastago',
            'client_profile_id': owner.pk,
        }, format='json')

        assert response.status_code == 201, response.data
        assert response.data['name'] == 'Vastago'
        assert response.data['status'] == Project.STATUS_DEVELOPMENT
        assert response.data['status_label'] == 'En desarrollo'
        assert response.data['description'] == ''
        assert response.data['hostings_count'] == 0
        assert response.data['incomes_count'] == 0
        assert response.data['document_manager_enabled'] is True
        assert response.data['client']['profile_id'] == owner.pk
        project = Project.objects.get(pk=response.data['id'])
        assert project.client_id == owner.user_id

    def test_a_project_can_be_created_outside_the_document_manager(
        self, admin_client,
    ):
        owner = make_client('excluded@example.com')

        response = admin_client.post(CREATE_URL, {
            'name': 'PRUEBA',
            'client_profile_id': owner.pk,
            'document_manager_enabled': False,
        }, format='json')

        assert response.status_code == 201, response.data
        project = Project.objects.get(pk=response.data['id'])
        assert response.data['document_manager_enabled'] is False
        assert not hasattr(project, 'document_root_folder')

    def test_the_create_response_reports_the_clients_backlog(self, admin_client):
        """The inline-create flow (crear al vuelo from an accounting picker)
        decides whether to offer the assign modal from these two counters."""
        owner = make_client('deivis@example.com', first='Deivis', last='Ríos')
        make_income(client=owner)
        make_hosting(owner, None, name='Deivis - Vastago')

        response = admin_client.post(CREATE_URL, {
            'name': 'Vastago',
            'client_profile_id': owner.pk,
        }, format='json')

        assert response.status_code == 201, response.data
        assert response.data['unlinked_hostings_count'] == 1
        assert response.data['unlinked_incomes_count'] == 1

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
    def test_name_can_change(self, admin_client):
        owner = make_client('deivis@example.com')
        project = make_project(owner, 'Vastago')

        response = admin_client.patch(
            f'/api/projects/{project.pk}/update/',
            {'name': 'Vástago App'},
            format='json',
        )

        assert response.status_code == 200, response.data
        project.refresh_from_db()
        assert project.name == 'Vástago App'

    def test_description_can_change(self, admin_client):
        owner = make_client('deivis@example.com')
        project = make_project(owner, 'Vastago')

        response = admin_client.patch(
            f'/api/projects/{project.pk}/update/',
            {'description': 'App de gestión'},
            format='json',
        )

        assert response.status_code == 200, response.data
        project.refresh_from_db()
        assert project.description == 'App de gestión'

    def test_document_manager_visibility_can_change_without_deleting_content(
        self, admin_client,
    ):
        owner = make_client('documents@example.com')
        project = make_project(owner, 'Candle')
        root_id = project.document_root_folder.id

        response = admin_client.patch(
            f'/api/projects/{project.pk}/update/',
            {'document_manager_enabled': False},
            format='json',
        )

        assert response.status_code == 200, response.data
        project.refresh_from_db()
        assert project.document_manager_enabled is False
        assert project.document_root_folder.id == root_id

    def test_status_change_requires_the_transition_flow(self, admin_client):
        owner = make_client('deivis@example.com')
        project = make_project(owner, 'Vastago')

        response = admin_client.patch(
            f'/api/projects/{project.pk}/update/',
            {'status': Project.STATUS_SUSPENDED},
            format='json',
        )

        assert response.status_code == 400
        assert response.data['code'] == 'project_state_transition_required'
        project.refresh_from_db()
        assert project.status == Project.STATUS_ACTIVE

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

    def test_an_archived_project_stays_editable_for_manual_review(self, admin_client):
        owner = make_client('deivis@example.com')
        project = make_project(owner, 'Viejo', status=Project.STATUS_ARCHIVED)

        response = admin_client.patch(
            f'/api/projects/{project.pk}/update/',
            {'name': 'Renombrado'},
            format='json',
        )

        assert response.status_code == 200, response.data
        project.refresh_from_db()
        assert project.name == 'Renombrado'
        assert project.current_state_id is None
        assert project.state_review_required is True

    def test_update_cannot_jump_to_archived(self, admin_client):
        # Legacy enum writes never bypass the previewed lifecycle transition.
        owner = make_client('deivis@example.com')
        project = make_project(owner, 'Vastago')

        response = admin_client.patch(
            f'/api/projects/{project.pk}/update/',
            {'status': Project.STATUS_ARCHIVED},
            format='json',
        )

        assert response.status_code == 400
        assert response.data['code'] == 'project_state_transition_required'


class TestArchivePanelProject:
    @pytest.mark.parametrize('action', ('archive', 'unarchive'))
    def test_legacy_archive_endpoints_are_gone(self, admin_client, action):
        owner = make_client('deivis@example.com')
        project = make_project(owner, 'Vastago')

        response = admin_client.patch(f'/api/projects/{project.pk}/{action}/')

        assert response.status_code == 410
        assert response.data['code'] == 'project_archive_replaced'
        project.refresh_from_db()
        assert project.status == Project.STATUS_ACTIVE


class TestProjectAuditTrail:
    """Every project mutation leaves a PROJECT row (requisito 12): before
    this, /panel/projects wrote no audit at all."""

    def _rows(self, project_id):
        from content.models import AccountingChangeLog

        return AccountingChangeLog.objects.filter(
            entity_type='project', object_id=project_id,
        ).order_by('created_at')

    def test_create_and_update_are_audited(self, admin_client):
        owner = make_client('deivis@example.com', first='Deivis', last='Ríos')

        created = admin_client.post(CREATE_URL, {
            'name': 'Vastago', 'client_profile_id': owner.pk,
        }, format='json')
        project_id = created.data['id']
        admin_client.patch(
            f'/api/projects/{project_id}/update/',
            {'name': 'Vastago v2'}, format='json',
        )

        rows = list(self._rows(project_id))
        assert [row.action for row in rows] == ['created', 'updated']
        name_change = next(
            c for c in rows[1].changes if c['field'] == 'name'
        )
        assert (name_change['old'], name_change['new']) == ('Vastago', 'Vastago v2')

    def test_a_noop_update_writes_nothing(self, admin_client):
        owner = make_client('deivis@example.com')
        project = make_project(owner, 'Vastago')

        admin_client.patch(
            f'/api/projects/{project.pk}/update/',
            {'name': 'Vastago'}, format='json',
        )

        assert self._rows(project.pk).count() == 0
