"""Focused contract tests for the paginated document-manager endpoint."""

from datetime import UTC, datetime

import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model
from django.urls import reverse

from content.models import (
    Document,
    DocumentFolder,
    DocumentNote,
    DocumentState,
    DocumentStateEpisode,
    DocumentStateEpisodeEvent,
    DocumentStateGroup,
    DocumentType,
)

pytestmark = pytest.mark.django_db

TEST_EVENT_AT = datetime(2020, 1, 1, tzinfo=UTC)


@pytest.fixture
def markdown_type():
    return DocumentType.objects.create(
        code='browse-markdown', name='Browse markdown',
    )


@pytest.fixture
def browse_url():
    return reverse('browse-documents')


@pytest.fixture
def project_root(markdown_type):
    user = get_user_model().objects.create_user(
        username='browse-client@example.com',
        email='browse-client@example.com',
    )
    profile = UserProfile.objects.create(user=user, cedula='9000000001')
    project = Project.objects.create(name='Proyecto browse', client=user)
    root = project.document_root_folder
    child = DocumentFolder.objects.create(
        name='Fase uno', parent=root, project=project, client_user=user,
    )
    root_document = Document.objects.create(
        title='Documento en raíz', document_type=markdown_type,
        project=project, client_user=user, folder=root,
    )
    child_document = Document.objects.create(
        title='Documento descendiente', document_type=markdown_type,
        project=project, client_user=user, folder=child,
    )
    return {
        'profile': profile,
        'project': project,
        'root_document': root_document,
        'child_document': child_document,
    }


def test_returns_first_server_page(admin_client, browse_url, markdown_type):
    Document.objects.bulk_create([
        Document(title=f'Documento {index:02}', document_type=markdown_type)
        for index in range(13)
    ])

    response = admin_client.get(browse_url, {'page': 1, 'page_size': 10})

    data = response.json()
    assert response.status_code == 200
    assert len(data['results']) == 10
    assert data['count'] == 13
    assert data['total_pages'] == 2


def test_clamps_out_of_range_page(admin_client, browse_url, markdown_type):
    Document.objects.bulk_create([
        Document(title=f'Documento {index:02}', document_type=markdown_type)
        for index in range(11)
    ])

    response = admin_client.get(browse_url, {'page': 99, 'page_size': 10})

    data = response.json()
    assert data['page'] == 2
    assert len(data['results']) == 1


def test_rejects_unsupported_page_size(admin_client, browse_url):
    response = admin_client.get(browse_url, {'page_size': 50})

    assert response.status_code == 400
    assert 'page_size' in response.json()


def test_filters_numeric_folder_before_paging(
    admin_client, browse_url, markdown_type,
):
    selected = DocumentFolder.objects.create(name='Seleccionada')
    other = DocumentFolder.objects.create(name='Otra')
    expected = Document.objects.create(
        title='Visible', document_type=markdown_type, folder=selected,
    )
    Document.objects.create(
        title='Oculto', document_type=markdown_type, folder=other,
    )

    response = admin_client.get(browse_url, {'folder': selected.id})

    assert [row['id'] for row in response.json()['results']] == [expected.id]


def test_project_root_excludes_descendant_documents(
    admin_client, browse_url, project_root,
):
    response = admin_client.get(browse_url, {
        'folder': 'root',
        'project': project_root['project'].id,
    })

    ids = {row['id'] for row in response.json()['results']}
    assert project_root['child_document'].id not in ids


def test_project_root_keeps_managed_root_documents(
    admin_client, browse_url, project_root,
):
    response = admin_client.get(browse_url, {
        'folder': 'root',
        'project': project_root['project'].id,
    })

    ids = {row['id'] for row in response.json()['results']}
    assert project_root['root_document'].id in ids


def test_archived_project_root_excludes_archived_descendant_documents(
    admin_client, browse_url, project_root,
):
    Document.objects.filter(pk__in=[
        project_root['root_document'].pk,
        project_root['child_document'].pk,
    ]).update(is_archived=True, archived_at=TEST_EVENT_AT)

    response = admin_client.get(browse_url, {
        'scope': 'archived',
        'folder': 'root',
        'project': project_root['project'].id,
    })

    ids = {row['id'] for row in response.json()['results']}
    assert project_root['root_document'].id in ids
    assert project_root['child_document'].id not in ids


@pytest.mark.parametrize('page', [0, 'not-a-page'])
def test_rejects_invalid_page(admin_client, browse_url, page):
    response = admin_client.get(browse_url, {'page': page})

    assert response.status_code == 400
    assert 'page' in response.json()


def test_rejects_authenticated_non_staff_user(api_client, browse_url):
    user = get_user_model().objects.create_user(
        username='browse-non-staff@example.com',
        email='browse-non-staff@example.com',
        is_staff=False,
    )
    api_client.force_authenticate(user=user)

    response = api_client.get(browse_url)

    assert response.status_code == 403


def test_compact_states_omit_history_fields(
    admin_client, browse_url, markdown_type,
):
    document = Document.objects.create(
        title='Con estado', document_type=markdown_type,
    )
    group = DocumentStateGroup.objects.create(name='Browse compacto')
    state = DocumentState.objects.create(
        name='Browse revisión', group=group, color='blue',
    )
    episode = DocumentStateEpisode.objects.create(
        document=document,
        state=state,
        opened_at=TEST_EVENT_AT,
    )
    DocumentStateEpisodeEvent.objects.create(
        episode=episode,
        event_type=DocumentStateEpisodeEvent.EventType.OPENED,
    )
    DocumentNote.objects.create(
        document=document, episode=episode, content='Pendiente interno',
    )

    response = admin_client.get(browse_url)

    active_state = response.json()['results'][0]['active_states'][0]
    assert set(active_state) == {'id', 'state', 'opened_at', 'duration_seconds'}
    assert 'events' not in active_state
    assert 'notes' not in active_state


def test_query_count_stays_constant(
    admin_client,
    browse_url,
    markdown_type,
    django_assert_max_num_queries,
):
    documents = Document.objects.bulk_create([
        Document(title=f'Con estado {index}', document_type=markdown_type)
        for index in range(10)
    ])
    group = DocumentStateGroup.objects.create(name='Browse consultas')
    state = DocumentState.objects.create(name='Browse validar', group=group)
    DocumentStateEpisode.objects.bulk_create([
        DocumentStateEpisode(
            document=document,
            state=state,
            opened_at=TEST_EVENT_AT,
        )
        for document in documents
    ])

    with django_assert_max_num_queries(4):
        response = admin_client.get(browse_url, {'page_size': 10})

    assert response.status_code == 200


def test_project_root_query_count_stays_bounded_with_active_states(
    admin_client,
    browse_url,
    markdown_type,
    project_root,
    django_assert_max_num_queries,
):
    project = project_root['project']
    documents = [project_root['root_document']]
    documents.extend(Document.objects.bulk_create([
        Document(
            title=f'Proyecto con estado {index}',
            document_type=markdown_type,
            project=project,
            client_user=project.client,
            folder=project.document_root_folder,
        )
        for index in range(9)
    ]))
    group = DocumentStateGroup.objects.create(name='Browse proyecto consultas')
    state = DocumentState.objects.create(
        name='Browse proyecto validar', group=group,
    )
    DocumentStateEpisode.objects.bulk_create([
        DocumentStateEpisode(
            document=document,
            state=state,
            opened_at=TEST_EVENT_AT,
        )
        for document in documents
    ])

    with django_assert_max_num_queries(6):
        response = admin_client.get(browse_url, {
            'folder': 'root',
            'project': project.id,
            'page_size': 10,
        })

    assert response.status_code == 200
