"""Query-budget contracts for archived requirements."""

import pytest
from content.models import BusinessProposal
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from accounts.models import (
    Project,
    ProjectPhase,
    Requirement,
    RequirementComment,
    RequirementHistory,
    UserProfile,
)

User = get_user_model()


def _detail_url(project_id, requirement_id):
    return f'/api/accounts/projects/{project_id}/requirements/{requirement_id}/'


def _create_detail_relations(requirement, count, *, start):
    authors = User.objects.bulk_create([
        User(
            username=f'archive-budget-{index}@example.com',
            email=f'archive-budget-{index}@example.com',
        )
        for index in range(start, start + count)
    ])
    RequirementComment.objects.bulk_create([
        RequirementComment(
            requirement=requirement,
            user=author,
            content=f'Archive budget comment {index}',
        )
        for index, author in zip(range(start, start + count), authors)
    ])
    RequirementHistory.objects.bulk_create([
        RequirementHistory(
            requirement=requirement,
            from_status=Requirement.STATUS_BACKLOG,
            to_status=Requirement.STATUS_IN_PROGRESS,
            changed_by=author,
        )
        for author in authors
    ])


def _captured_sql(queries):
    return '\n'.join(query['sql'].lower() for query in queries)


@pytest.fixture
def api_client():
    """Provide a client for authenticated archive requests."""
    return APIClient()


@pytest.fixture
def admin_user():
    """Create the administrator allowed to archive requirements."""
    user = User.objects.create_user(
        username='archive-budget-admin@example.com',
        email='archive-budget-admin@example.com',
        password='archivepass1',
    )
    UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_ADMIN,
        is_onboarded=True,
        profile_completed=True,
    )
    return user


@pytest.fixture
def admin_headers(api_client, admin_user):
    """Authenticate the administrator through the JWT login endpoint."""
    response = api_client.post('/api/accounts/login/', {
        'email': admin_user.email,
        'password': 'archivepass1',
    })
    return {'HTTP_AUTHORIZATION': f"Bearer {response.json()['tokens']['access']}"}


@pytest.fixture
def archive_requirements(admin_user):
    """Create todo, in-progress, and completed requirements for progress recalculation."""
    project = Project.objects.create(
        name='Archive query budget project',
        client=admin_user,
        status=Project.STATUS_ACTIVE,
    )
    proposal = BusinessProposal.objects.create(
        title='Archive query budget proposal',
        client_name='Archive query budget client',
    )
    phase = ProjectPhase.objects.create(project=project, business_proposal=proposal, order=1)
    one_relation_requirement = Requirement.objects.create(
        phase=phase,
        title='One relation requirement',
        status=Requirement.STATUS_TODO,
    )
    fifty_relation_requirement = Requirement.objects.create(
        phase=phase,
        title='Fifty relation requirement',
        status=Requirement.STATUS_IN_PROGRESS,
    )
    Requirement.objects.create(
        phase=phase,
        title='Completed requirement',
        status=Requirement.STATUS_DONE,
    )
    return project, one_relation_requirement, fifty_relation_requirement


@pytest.mark.django_db
def test_requirement_delete_avoids_detail_relation_queries(
    api_client, admin_headers, archive_requirements, record_property,
):
    """Fails if archiving a requirement reloads its comments or history."""
    project, one_relation_requirement, fifty_relation_requirement = archive_requirements
    _create_detail_relations(one_relation_requirement, 1, start=0)
    _create_detail_relations(fifty_relation_requirement, 50, start=100)

    with CaptureQueriesContext(connection) as one_relation_queries:
        one_relation_response = api_client.delete(
            _detail_url(project.id, one_relation_requirement.id),
            **admin_headers,
        )

    with CaptureQueriesContext(connection) as fifty_relation_queries:
        fifty_relation_response = api_client.delete(
            _detail_url(project.id, fifty_relation_requirement.id),
            **admin_headers,
        )

    one_relation_requirement.refresh_from_db()
    fifty_relation_requirement.refresh_from_db()
    project.refresh_from_db()
    fifty_relation_sql = _captured_sql(fifty_relation_queries)
    record_property('query_count_one', len(one_relation_queries))
    record_property('query_count_fifty', len(fifty_relation_queries))

    assert (one_relation_response.status_code, fifty_relation_response.status_code) == (200, 200)
    assert (one_relation_response.json(), fifty_relation_response.json()) == (
        {'detail': 'Requerimiento archivado.'},
        {'detail': 'Requerimiento archivado.'},
    )
    assert (one_relation_requirement.is_archived, fifty_relation_requirement.is_archived) == (True, True)
    assert project.progress == 100
    assert len(one_relation_queries) == len(fifty_relation_queries)
    assert 'accounts_requirementcomment' not in fifty_relation_sql
    assert 'accounts_requirementhistory' not in fifty_relation_sql
