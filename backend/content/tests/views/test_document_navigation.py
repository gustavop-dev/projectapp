"""Aggregated project/client navigation for the document manager."""

from datetime import timedelta

import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model
from django.db import connection
from django.urls import reverse
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from content.models import (
    Document,
    DocumentFolder,
    DocumentState,
    DocumentStateGroup,
    DocumentType,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def markdown_doc_type(db):
    document_type, _created = DocumentType.objects.get_or_create(
        code='markdown',
        defaults={'name': 'Markdown', 'label': 'Markdown'},
    )
    return document_type


def make_client(email, *, company='', inactive=False):
    user = get_user_model().objects.create_user(
        username=email,
        email=email,
        password='pass12345',
    )
    profile = UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
        company_name=company,
        deactivated_at=timezone.now() if inactive else None,
    )
    return profile


def make_project_state(*, effect):
    group = DocumentStateGroup.objects.create(
        catalog=DocumentStateGroup.Catalog.PROJECTS,
        name=f'Estado {effect}',
    )
    return DocumentState.objects.create(
        catalog=DocumentStateGroup.Catalog.PROJECTS,
        group=group,
        name=f'Estado {effect}',
        color=DocumentState.Color.GRAY,
        operational_effect=effect,
    )


def make_navigation_entry(email, *, document_type):
    profile = make_client(email, company=email.partition('@')[0])
    project = Project.objects.create(
        name=f'Project {profile.pk}', client=profile.user,
    )
    return Document.objects.create(
        title=f'Document {profile.pk}', document_type=document_type,
        project=project, client_user=profile.user,
    )


@pytest.fixture
def navigation_setup(db, markdown_doc_type):
    acme = make_client('acme@test.com', company='ACME')
    legacy = make_client('legacy@test.com', company='Legacy', inactive=True)
    visible_state = make_project_state(
        effect=DocumentState.OperationalEffect.DEVELOPMENT,
    )
    hidden_state = make_project_state(
        effect=DocumentState.OperationalEffect.SUSPENDED,
    )
    alpha = Project.objects.create(
        name='Alpha', client=acme.user, current_state=visible_state,
    )
    hidden = Project.objects.create(
        name='Hidden', client=legacy.user, current_state=hidden_state,
    )

    root = alpha.document_root_folder
    child = DocumentFolder.objects.create(
        name='Nested', parent=root, project=alpha, client_user=acme.user,
    )
    archived_child = DocumentFolder.objects.create(
        name='Archived nested', parent=root, project=alpha,
        client_user=acme.user, is_archived=True,
        archived_at=timezone.now() - timedelta(days=1),
    )
    legacy_folder = hidden.document_root_folder
    unassigned_folder = DocumentFolder.objects.create(name='Internal')

    active_document = Document.objects.create(
        title='Alpha brief', document_type=markdown_doc_type,
        folder=child, project=alpha, client_user=acme.user,
    )
    archived_document = Document.objects.create(
        title='Alpha archive', document_type=markdown_doc_type,
        folder=archived_child, project=alpha, client_user=acme.user,
        is_archived=True, archived_at=timezone.now(),
    )
    client_only_document = Document.objects.create(
        title='Legacy contract', document_type=markdown_doc_type,
        client_user=legacy.user,
    )
    second_client_only_document = Document.objects.create(
        title='Legacy invoice', document_type=markdown_doc_type,
        client_user=legacy.user,
    )
    project_only_document = Document.objects.create(
        title='Hidden project note', document_type=markdown_doc_type,
        project=hidden,
    )
    free_document = Document.objects.create(
        title='Internal template', document_type=markdown_doc_type,
    )
    return {
        'acme': acme,
        'legacy': legacy,
        'alpha': alpha,
        'hidden': hidden,
        'root': root,
        'legacy_folder': legacy_folder,
        'unassigned_folder': unassigned_folder,
        'active_document': active_document,
        'archived_document': archived_document,
        'client_only_document': client_only_document,
        'second_client_only_document': second_client_only_document,
        'project_only_document': project_only_document,
        'free_document': free_document,
    }


def find_entry(entries, entry_id):
    return next(entry for entry in entries if entry['id'] == entry_id)


def test_navigation_counts_each_nested_item_once(
    admin_client, navigation_setup,
):
    response = admin_client.get(reverse('document-navigation'))

    assert response.status_code == 200
    data = response.json()
    assert data['totals'] == {
        'active': {'folders': 12, 'documents': 5},
        'archived': {'folders': 1, 'documents': 1},
    }
    alpha = find_entry(data['projects'], navigation_setup['alpha'].id)
    assert alpha['counts'] == {
        'active': {'folders': 6, 'documents': 1},
        'archived': {'folders': 1, 'documents': 1},
    }
    assert alpha['managed_root_id'] == navigation_setup['root'].id
    assert alpha['is_visible'] is True
    assert alpha['catalog_bucket'] == 'active'


def test_navigation_counts_client_only_documents_as_project_unassigned(
    admin_client, navigation_setup,
):
    """Falla si el inventario sin proyecto reutiliza el bucket sin cliente."""
    data = admin_client.get(reverse('document-navigation')).json()

    assert data['unassigned']['project'] == {
        'active': {'folders': 1, 'documents': 3},
        'archived': {'folders': 0, 'documents': 0},
    }
    assert data['unassigned']['client'] == {
        'active': {'folders': 1, 'documents': 2},
        'archived': {'folders': 0, 'documents': 0},
    }


def test_navigation_includes_inactive_clients_with_content(
    admin_client, navigation_setup,
):
    data = admin_client.get(reverse('document-navigation')).json()

    legacy = find_entry(data['clients'], navigation_setup['legacy'].id)
    assert legacy['name'] == 'Legacy'
    assert legacy['is_inactive'] is True
    assert legacy['catalog_bucket'] == 'archived'
    assert legacy['counts']['active'] == {'folders': 5, 'documents': 2}


def test_navigation_groups_suspended_projects_as_archived_without_hiding_them(
    admin_client, navigation_setup,
):
    data = admin_client.get(reverse('document-navigation')).json()

    hidden = find_entry(data['projects'], navigation_setup['hidden'].id)
    assert hidden['is_visible'] is True
    assert hidden['catalog_bucket'] == 'archived'
    assert hidden['counts']['active'] == {'folders': 5, 'documents': 1}


def test_navigation_query_count_does_not_scale_with_facet_entries(
    admin_client, navigation_setup, markdown_doc_type,
):
    """Falla si cada proyecto o cliente obliga a consultar su usuario aparte."""
    url = reverse('document-navigation')
    admin_client.get(url)

    with CaptureQueriesContext(connection) as baseline:
        assert admin_client.get(url).status_code == 200

    make_navigation_entry('growth-one@test.com', document_type=markdown_doc_type)
    make_navigation_entry('growth-two@test.com', document_type=markdown_doc_type)
    make_navigation_entry('growth-three@test.com', document_type=markdown_doc_type)

    with CaptureQueriesContext(connection) as grown:
        response = admin_client.get(url)

    assert response.status_code == 200
    assert len(response.json()['projects']) == 5
    assert len(grown) == len(baseline)


def test_navigation_includes_clients_without_content(
    admin_client, navigation_setup,
):
    empty_client = make_client('empty@test.com', company='Empty')
    data = admin_client.get(reverse('document-navigation')).json()

    entry = find_entry(data['clients'], empty_client.id)
    assert entry['counts'] == {
        'active': {'folders': 0, 'documents': 0},
        'archived': {'folders': 0, 'documents': 0},
    }


def test_navigation_counts_automatic_project_roots(
    admin_client, navigation_setup,
):
    project_client = make_client('root-only@test.com', company='Root only')
    empty_project = Project.objects.create(
        name='Empty project', client=project_client.user,
    )
    data = admin_client.get(reverse('document-navigation')).json()

    client_entry = find_entry(data['clients'], project_client.id)
    assert client_entry['counts']['active'] == {'folders': 5, 'documents': 0}
    empty_entry = find_entry(data['projects'], empty_project.id)
    assert empty_entry['counts']['active'] == {'folders': 5, 'documents': 0}


def test_navigation_includes_a_historical_project_without_a_root(
    admin_client, navigation_setup,
):
    historical_client = make_client('vastago@test.com', company='Vástago')
    historical = Project.objects.create(
        name='Vástago', client=historical_client.user,
    )
    historical.document_root_folder.children.all().delete()
    historical.document_root_folder.delete()

    data = admin_client.get(reverse('document-navigation')).json()

    entry = find_entry(data['projects'], historical.id)
    assert entry['managed_root_id'] is None
    assert entry['counts']['active'] == {'folders': 0, 'documents': 0}


def test_navigation_includes_prueba_without_any_opt_out(
    admin_client, navigation_setup,
):
    prueba_client = make_client('prueba@test.com', company='PRUEBA')
    prueba = Project.objects.create(name='PRUEBA', client=prueba_client.user)

    data = admin_client.get(reverse('document-navigation')).json()

    entry = find_entry(data['projects'], prueba.id)
    assert entry['name'] == 'PRUEBA'
    assert entry['counts']['active'] == {'folders': 5, 'documents': 0}


def test_navigation_requires_admin_auth(api_client):
    response = api_client.get(reverse('document-navigation'))

    assert response.status_code == 401
