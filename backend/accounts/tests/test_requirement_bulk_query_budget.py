"""Query-budget contract for bulk requirement uploads."""
from decimal import Decimal

import pytest
from content.models import BusinessProposal
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from accounts.models import Project, ProjectPhase, Requirement, UserProfile

User = get_user_model()


def _bulk_url(project_id, phase_id):
    return f'/api/accounts/projects/{project_id}/requirements/bulk/?phase_id={phase_id}'


def _requirement_payloads(count):
    return [{'title': f'Imported requirement {index}'} for index in range(count)]


def _select_queries(queries):
    """Return the read statements captured during an API request."""
    return [query['sql'] for query in queries if query['sql'].lstrip().upper().startswith('SELECT')]


def _requirement_inserts(queries):
    """Return Requirement insert statements without counting unrelated signal writes."""
    table_name = Requirement._meta.db_table.upper()
    return [
        query['sql'] for query in queries
        if query['sql'].lstrip().upper().startswith(f'INSERT INTO "{table_name}"')
    ]


@pytest.fixture
def api_client():
    """Provide an API client for the authenticated upload requests."""
    return APIClient()


@pytest.fixture
def admin_headers(api_client):
    """Authenticate a platform administrator with the production JWT flow."""
    admin = User.objects.create_user(
        username='bulk-budget-admin@example.com',
        email='bulk-budget-admin@example.com',
        password='pass12345',
    )
    UserProfile.objects.create(
        user=admin,
        role=UserProfile.ROLE_ADMIN,
        is_onboarded=True,
        profile_completed=True,
    )
    login = api_client.post('/api/accounts/login/', {
        'email': admin.email,
        'password': 'pass12345',
    })
    return {'HTTP_AUTHORIZATION': f"Bearer {login.json()['tokens']['access']}"}


@pytest.fixture
def project_phase():
    """Create the project phase and proposal represented in bulk upload responses."""
    client = User.objects.create_user(
        username='bulk-budget-client@example.com',
        email='bulk-budget-client@example.com',
        password='pass12345',
    )
    UserProfile.objects.create(
        user=client,
        role=UserProfile.ROLE_CLIENT,
        is_onboarded=True,
        profile_completed=True,
    )
    project = Project.objects.create(name='Bulk budget project', client=client)
    proposal = BusinessProposal.objects.create(
        title='Bulk budget proposal',
        client_name='Bulk budget client',
        total_investment=Decimal(12000000),
    )
    phase = ProjectPhase.objects.create(project=project, business_proposal=proposal, order=1)
    return project, phase


@pytest.mark.django_db
def test_bulk_upload_limits_comment_reads_as_upload_size_grows(
    api_client, admin_headers, project_phase,
):
    """Fails if serializing new requirements counts comments once per uploaded row."""
    project, phase = project_phase

    with CaptureQueriesContext(connection) as one_requirement_queries:
        one_response = api_client.post(
            _bulk_url(project.id, phase.id),
            _requirement_payloads(1),
            format='json',
            **admin_headers,
        )

    with CaptureQueriesContext(connection) as five_hundred_requirement_queries:
        five_hundred_response = api_client.post(
            _bulk_url(project.id, phase.id),
            _requirement_payloads(500),
            format='json',
            **admin_headers,
        )

    one_body = one_response.json()
    five_hundred_body = five_hundred_response.json()
    one_selects = _select_queries(one_requirement_queries.captured_queries)
    five_hundred_selects = _select_queries(five_hundred_requirement_queries.captured_queries)
    comment_table = 'accounts_requirementcomment'

    assert (one_response.status_code, five_hundred_response.status_code) == (201, 201)
    assert [
        (body['created'], len(body['requirements']))
        for body in (one_body, five_hundred_body)
    ] == [(1, 1), (500, 500)]
    assert [item['comments_count'] for item in one_body['requirements']] == [0]
    assert {item['comments_count'] for item in five_hundred_body['requirements']} == {0}
    assert {item['phase_title'] for item in five_hundred_body['requirements']} == {'Bulk budget proposal'}
    assert len(one_selects) == len(five_hundred_selects)
    assert comment_table not in '\n'.join(one_selects + five_hundred_selects).lower()


@pytest.mark.django_db
def test_bulk_upload_uses_one_requirement_insert_for_each_uploaded_row(
    api_client, admin_headers, project_phase,
):
    """Fails if bulk upload stops preserving the endpoint's individual Requirement creates."""
    project, phase = project_phase

    with CaptureQueriesContext(connection) as captured_queries:
        response = api_client.post(
            _bulk_url(project.id, phase.id),
            _requirement_payloads(500),
            format='json',
            **admin_headers,
        )

    assert response.status_code == 201
    assert response.json()['created'] == 500
    assert len(_requirement_inserts(captured_queries.captured_queries)) == 500


@pytest.mark.django_db
def test_bulk_replace_returns_new_requirements_after_removing_phase_rows(
    api_client, admin_headers, project_phase,
):
    """Fails if replace no longer removes prior phase requirements before serializing new rows."""
    project, phase = project_phase
    previous_requirements = Requirement.objects.bulk_create([
        Requirement(phase=phase, title='Prior requirement one'),
        Requirement(phase=phase, title='Prior requirement two'),
    ])

    response = api_client.post(
        f'{_bulk_url(project.id, phase.id)}&mode=replace',
        [{'title': 'Replacement one'}, {'title': 'Replacement two'}],
        format='json',
        **admin_headers,
    )

    body = response.json()
    assert response.status_code == 201
    assert (body['mode'], body['deleted'], body['created']) == ('replace', 2, 2)
    assert [item['title'] for item in body['requirements']] == ['Replacement one', 'Replacement two']
    assert {item['comments_count'] for item in body['requirements']} == {0}
    assert not Requirement.objects.filter(pk__in=[item.pk for item in previous_requirements]).exists()


@pytest.mark.django_db
def test_bulk_upload_rejects_501_rows_without_changing_phase_requirements(
    api_client, admin_headers, project_phase,
):
    """Fails if the upload limit validates after creating or deleting requirements."""
    project, phase = project_phase
    existing = Requirement.objects.create(phase=phase, title='Existing requirement')

    response = api_client.post(
        f'{_bulk_url(project.id, phase.id)}&mode=replace',
        _requirement_payloads(501),
        format='json',
        **admin_headers,
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'Máximo 500 requerimientos por carga.'
    assert list(Requirement.objects.filter(phase=phase).values_list('id', 'title')) == [
        (existing.id, 'Existing requirement'),
    ]
