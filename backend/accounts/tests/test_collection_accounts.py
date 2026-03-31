from decimal import Decimal

import pytest

from accounts.models import Project
from content.models import Document, DocumentCollectionAccount
from content.services.document_type_codes import COLLECTION_ACCOUNT
from content.services.document_type_utils import get_collection_account_document_type


@pytest.mark.django_db
def test_admin_creates_collection_account_draft(api_client, admin_headers, project):
    resp = api_client.post(
        '/api/accounts/collection-accounts/',
        {
            'title': 'Invoice one',
            'project_id': project.id,
            'payment_term_days': 15,
        },
        format='json',
        **admin_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data['commercial_status'] == 'draft'
    assert data['document_type']['code'] == COLLECTION_ACCOUNT


@pytest.mark.django_db
def test_client_list_excludes_draft_collection_accounts(
    api_client, admin_headers, client_headers, project,
):
    api_client.post(
        '/api/accounts/collection-accounts/',
        {'title': 'Hidden draft', 'project_id': project.id},
        format='json',
        **admin_headers,
    )
    resp = api_client.get('/api/accounts/collection-accounts/', **client_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.django_db
def test_issue_then_client_sees_account(
    api_client, admin_headers, client_headers, project,
):
    create = api_client.post(
        '/api/accounts/collection-accounts/',
        {'title': 'Issued doc', 'project_id': project.id, 'payment_term_days': 5},
        format='json',
        **admin_headers,
    )
    assert create.status_code == 201
    aid = create.json()['id']

    patch = api_client.patch(
        f'/api/accounts/collection-accounts/{aid}/',
        {
            'items': [
                {
                    'description': 'Dev milestone',
                    'quantity': '1',
                    'unit_price': '100000.00',
                    'discount_amount': '0',
                    'tax_amount': '0',
                    'line_total': '100000.00',
                },
            ],
        },
        format='json',
        **admin_headers,
    )
    assert patch.status_code == 200

    issue = api_client.post(
        f'/api/accounts/collection-accounts/{aid}/issue/',
        format='json',
        **admin_headers,
    )
    assert issue.status_code == 200
    assert issue.json()['commercial_status'] == 'issued'
    assert issue.json()['public_number']

    lst = api_client.get('/api/accounts/collection-accounts/', **client_headers)
    assert len(lst.json()) == 1
    assert lst.json()[0]['id'] == aid


@pytest.mark.django_db
def test_client_cannot_patch_collection_account(
    api_client, admin_headers, client_headers, project,
):
    create = api_client.post(
        '/api/accounts/collection-accounts/',
        {'title': 'Doc', 'project_id': project.id},
        format='json',
        **admin_headers,
    )
    aid = create.json()['id']
    api_client.post(
        f'/api/accounts/collection-accounts/{aid}/issue/',
        format='json',
        **admin_headers,
    )
    resp = api_client.patch(
        f'/api/accounts/collection-accounts/{aid}/',
        {'title': 'Hacked'},
        format='json',
        **client_headers,
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_mark_paid_from_issued(api_client, admin_headers, project):
    create = api_client.post(
        '/api/accounts/collection-accounts/',
        {'title': 'Pay me', 'project_id': project.id},
        format='json',
        **admin_headers,
    )
    aid = create.json()['id']
    api_client.post(
        f'/api/accounts/collection-accounts/{aid}/issue/',
        format='json',
        **admin_headers,
    )
    resp = api_client.post(
        f'/api/accounts/collection-accounts/{aid}/mark-paid/',
        format='json',
        **admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()['commercial_status'] == 'paid'


@pytest.mark.django_db
def test_commercial_is_overdue_derived(project, client_user):
    dt = get_collection_account_document_type()
    doc = Document.objects.create(
        title='Overdue test',
        document_type=dt,
        commercial_status=Document.CommercialStatus.ISSUED,
        project=project,
        client_user=client_user,
        due_date='2020-01-01',
        total=Decimal('1'),
    )
    DocumentCollectionAccount.objects.create(document=doc)
    from content.services.collection_account_service import commercial_is_overdue

    assert commercial_is_overdue(doc) is True


@pytest.mark.django_db
def test_get_collection_account_detail_returns_404_for_unknown_id(api_client, admin_headers):
    resp = api_client.get(
        '/api/accounts/collection-accounts/999999/',
        **admin_headers,
    )

    assert resp.status_code == 404


@pytest.mark.django_db
def test_get_collection_account_pdf_returns_pdf_attachment_when_issued(
    api_client, admin_headers, project,
):
    create = api_client.post(
        '/api/accounts/collection-accounts/',
        {'title': 'PDF doc', 'project_id': project.id},
        format='json',
        **admin_headers,
    )
    aid = create.json()['id']
    api_client.post(
        f'/api/accounts/collection-accounts/{aid}/issue/',
        format='json',
        **admin_headers,
    )

    resp = api_client.get(
        f'/api/accounts/collection-accounts/{aid}/pdf/',
        **admin_headers,
    )

    assert resp.status_code == 200
    assert resp['Content-Type'] == 'application/pdf'
    assert resp.content[:4] == b'%PDF'


@pytest.mark.django_db
def test_issue_collection_account_returns_400_when_no_issuer_profile_exists(
    api_client, admin_headers, project,
):
    from content.models import IssuerProfile

    IssuerProfile.objects.all().delete()
    create = api_client.post(
        '/api/accounts/collection-accounts/',
        {'title': 'No issuer', 'project_id': project.id},
        format='json',
        **admin_headers,
    )
    aid = create.json()['id']

    resp = api_client.post(
        f'/api/accounts/collection-accounts/{aid}/issue/',
        format='json',
        **admin_headers,
    )

    assert resp.status_code == 400
    assert 'issuer' in resp.json()['detail'].lower()


@pytest.mark.django_db
def test_client_post_collection_account_returns_403(api_client, client_headers, project):
    resp = api_client.post(
        '/api/accounts/collection-accounts/',
        {'title': 'Blocked', 'project_id': project.id},
        format='json',
        **client_headers,
    )

    assert resp.status_code == 403


@pytest.mark.django_db
def test_admin_list_collection_accounts_filters_by_project_id_query_param(
    api_client, admin_headers, project,
):
    other = Project.objects.create(
        name='Other CA project',
        client=project.client,
        status=Project.STATUS_ACTIVE,
        progress=0,
    )
    api_client.post(
        '/api/accounts/collection-accounts/',
        {'title': 'On target project', 'project_id': project.id},
        format='json',
        **admin_headers,
    )
    api_client.post(
        '/api/accounts/collection-accounts/',
        {'title': 'On other project', 'project_id': other.id},
        format='json',
        **admin_headers,
    )

    resp = api_client.get(
        f'/api/accounts/collection-accounts/?project_id={project.id}',
        **admin_headers,
    )

    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]['title'] == 'On target project'


@pytest.mark.django_db
def test_client_get_pdf_for_draft_collection_account_returns_404(
    api_client, admin_headers, client_headers, project,
):
    create = api_client.post(
        '/api/accounts/collection-accounts/',
        {'title': 'Draft hidden', 'project_id': project.id},
        format='json',
        **admin_headers,
    )
    aid = create.json()['id']

    resp = api_client.get(
        f'/api/accounts/collection-accounts/{aid}/pdf/',
        **client_headers,
    )

    assert resp.status_code == 404


@pytest.mark.django_db
def test_create_collection_account_returns_400_when_project_id_is_invalid(
    api_client, admin_headers,
):
    resp = api_client.post(
        '/api/accounts/collection-accounts/',
        {'title': 'Bad project', 'project_id': 999999},
        format='json',
        **admin_headers,
    )

    assert resp.status_code == 400
    assert 'project_id' in resp.json()
