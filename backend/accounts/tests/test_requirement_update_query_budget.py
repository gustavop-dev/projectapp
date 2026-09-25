"""Query-budget contracts for requirement PATCH requests."""

import pytest
from content.models import BusinessProposal
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import (
    Project,
    ProjectPhase,
    ProjectScopeItem,
    Requirement,
    RequirementComment,
    RequirementHistory,
    UserProfile,
)

User = get_user_model()


def _detail_url(project_id, requirement_id):
    return f'/api/accounts/projects/{project_id}/requirements/{requirement_id}/'


def _relation_authors(count, *, start=0):
    return User.objects.bulk_create([
        User(
            username=f'requirement-update-author-{index}@example.com',
            email=f'requirement-update-author-{index}@example.com',
        )
        for index in range(start, start + count)
    ])


def _detail_relations(requirement, count, *, start=0):
    authors = _relation_authors(count, start=start)
    RequirementComment.objects.bulk_create([
        RequirementComment(
            requirement=requirement,
            user=author,
            content=f'Update budget comment {index}',
        )
        for index, author in enumerate(authors, start=start)
    ])
    RequirementHistory.objects.bulk_create([
        RequirementHistory(
            requirement=requirement,
            from_status=Requirement.STATUS_BACKLOG,
            to_status=Requirement.STATUS_TODO,
            changed_by=author,
        )
        for author in authors
    ])
    return {author.email for author in authors}


def _collection_selects(queries, model):
    table = model._meta.db_table.lower()
    return [
        query['sql']
        for query in queries
        if query['sql'].lstrip().upper().startswith('SELECT') and table in query['sql'].lower()
    ]


def _assert_response_scope_values(one_body, fifty_body, one_author_emails, fifty_author_emails):
    assert (
        (one_body['status'], one_body['scope_item_name'], one_body['scope_item_group_id']),
        (fifty_body['status'], fifty_body['scope_item_name'], fifty_body['scope_item_group_id']),
    ) == (
        (Requirement.STATUS_IN_PROGRESS, 'One update scope', 'one-update-group'),
        (Requirement.STATUS_IN_PROGRESS, 'Fifty update scope', 'fifty-update-group'),
    )
    assert (
        one_author_emails <= {entry['changed_by_email'] for entry in one_body['history']},
        fifty_author_emails <= {entry['changed_by_email'] for entry in fifty_body['history']},
    ) == (True, True)


def _assert_persisted_status_history(one_requirement, fifty_requirement):
    assert (
        (
            one_requirement.status,
            RequirementHistory.objects.filter(
                requirement=one_requirement,
                from_status=Requirement.STATUS_TODO,
                to_status=Requirement.STATUS_IN_PROGRESS,
            ).count(),
        ),
        (
            fifty_requirement.status,
            RequirementHistory.objects.filter(
                requirement=fifty_requirement,
                from_status=Requirement.STATUS_TODO,
                to_status=Requirement.STATUS_IN_PROGRESS,
            ).count(),
        ),
    ) == (
        (Requirement.STATUS_IN_PROGRESS, 1),
        (Requirement.STATUS_IN_PROGRESS, 1),
    )


def _assert_collection_select_counts(one_queries, fifty_queries):
    assert (
        len(_collection_selects(one_queries, RequirementComment)),
        len(_collection_selects(fifty_queries, RequirementComment)),
    ) == (1, 1)
    assert (
        len(_collection_selects(one_queries, RequirementHistory)),
        len(_collection_selects(fifty_queries, RequirementHistory)),
    ) == (1, 1)


@pytest.fixture
def api_client():
    """Provide an API client for JWT-authenticated requirement updates."""
    return APIClient()


@pytest.fixture
def users_and_headers(api_client):
    """Create administrator and client actors with real JWT credentials."""
    admin = User.objects.create_user(
        username='requirement-update-admin@example.com',
        email='requirement-update-admin@example.com',
        password=None,
    )
    UserProfile.objects.create(
        user=admin,
        role=UserProfile.ROLE_ADMIN,
        is_onboarded=True,
        profile_completed=True,
    )
    client = User.objects.create_user(
        username='requirement-update-client@example.com',
        email='requirement-update-client@example.com',
        password=None,
    )
    UserProfile.objects.create(
        user=client,
        role=UserProfile.ROLE_CLIENT,
        is_onboarded=True,
        profile_completed=True,
        created_by=admin,
    )
    admin_headers = {'HTTP_AUTHORIZATION': f'Bearer {AccessToken.for_user(admin)}'}
    client_headers = {'HTTP_AUTHORIZATION': f'Bearer {AccessToken.for_user(client)}'}
    return admin, admin_headers, client_headers, client


@pytest.fixture
def project_and_requirements(users_and_headers):
    """Create one- and fifty-relation requirements with visible scope metadata."""
    _, _, _, client = users_and_headers
    project = Project.objects.create(name='Requirement update budget project', client=client)
    proposal = BusinessProposal.objects.create(
        title='Requirement update budget proposal',
        client_name='Requirement update budget client',
    )
    phase = ProjectPhase.objects.create(project=project, business_proposal=proposal, order=1)
    one_scope_item = ProjectScopeItem.objects.create(
        phase=phase,
        source_item_id='one-update-scope',
        name='One update scope',
        group_id='one-update-group',
        group_title='One update group',
    )
    fifty_scope_item = ProjectScopeItem.objects.create(
        phase=phase,
        source_item_id='fifty-update-scope',
        name='Fifty update scope',
        group_id='fifty-update-group',
        group_title='Fifty update group',
    )
    one_relation_requirement = Requirement.objects.create(
        phase=phase,
        scope_item=one_scope_item,
        title='One relation requirement',
        status=Requirement.STATUS_TODO,
    )
    fifty_relation_requirement = Requirement.objects.create(
        phase=phase,
        scope_item=fifty_scope_item,
        title='Fifty relation requirement',
        status=Requirement.STATUS_TODO,
    )
    return project, one_relation_requirement, fifty_relation_requirement


@pytest.mark.django_db
def test_admin_status_patch_keeps_requirement_collection_reads_constant(
    api_client, users_and_headers, project_and_requirements, record_property,
):
    """Fails if a valid requirement PATCH reloads comments or history per related row."""
    _, admin_headers, _, _ = users_and_headers
    project, one_relation_requirement, fifty_relation_requirement = project_and_requirements
    one_author_emails = _detail_relations(one_relation_requirement, 1)
    fifty_author_emails = _detail_relations(fifty_relation_requirement, 50, start=1)

    with CaptureQueriesContext(connection) as one_relation_queries:
        one_relation_response = api_client.patch(
            _detail_url(project.id, one_relation_requirement.id),
            {'status': Requirement.STATUS_IN_PROGRESS},
            format='json',
            **admin_headers,
        )
    with CaptureQueriesContext(connection) as fifty_relation_queries:
        fifty_relation_response = api_client.patch(
            _detail_url(project.id, fifty_relation_requirement.id),
            {'status': Requirement.STATUS_IN_PROGRESS},
            format='json',
            **admin_headers,
        )

    one_relation_requirement.refresh_from_db()
    fifty_relation_requirement.refresh_from_db()
    one_body = one_relation_response.json()
    fifty_body = fifty_relation_response.json()
    record_property('query_count_one', len(one_relation_queries))
    record_property('query_count_fifty', len(fifty_relation_queries))

    assert (one_relation_response.status_code, fifty_relation_response.status_code) == (200, 200)
    _assert_response_scope_values(
        one_body,
        fifty_body,
        one_author_emails,
        fifty_author_emails,
    )
    _assert_persisted_status_history(one_relation_requirement, fifty_relation_requirement)
    assert len(one_relation_queries) == len(fifty_relation_queries)
    _assert_collection_select_counts(one_relation_queries, fifty_relation_queries)


@pytest.mark.django_db
def test_invalid_status_patch_skips_requirement_collection_reads(
    api_client, users_and_headers, project_and_requirements,
):
    """Fails if invalid requirement data prefetches comments or history before validation."""
    _, admin_headers, _, _ = users_and_headers
    project, one_relation_requirement, _ = project_and_requirements
    _detail_relations(one_relation_requirement, 1)

    with CaptureQueriesContext(connection) as queries:
        response = api_client.patch(
            _detail_url(project.id, one_relation_requirement.id),
            {'status': 'not-a-valid-status'},
            format='json',
            **admin_headers,
        )

    one_relation_requirement.refresh_from_db()
    assert response.status_code == 400
    assert 'status' in response.json()
    assert one_relation_requirement.status == Requirement.STATUS_TODO
    assert _collection_selects(queries, RequirementComment) == []
    assert _collection_selects(queries, RequirementHistory) == []


@pytest.mark.django_db
def test_client_status_patch_skips_requirement_collection_reads(
    api_client, users_and_headers, project_and_requirements,
):
    """Fails if a client requirement PATCH prefetches comments or history before authorization."""
    _, _, client_headers, _ = users_and_headers
    project, one_relation_requirement, _ = project_and_requirements
    _detail_relations(one_relation_requirement, 1)

    with CaptureQueriesContext(connection) as queries:
        response = api_client.patch(
            _detail_url(project.id, one_relation_requirement.id),
            {'status': Requirement.STATUS_IN_PROGRESS},
            format='json',
            **client_headers,
        )

    one_relation_requirement.refresh_from_db()
    assert response.status_code == 403
    assert response.json() == {'detail': 'Solo los administradores pueden modificar requerimientos.'}
    assert one_relation_requirement.status == Requirement.STATUS_TODO
    assert _collection_selects(queries, RequirementComment) == []
    assert _collection_selects(queries, RequirementHistory) == []
