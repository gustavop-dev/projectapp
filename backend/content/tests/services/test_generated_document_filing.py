from datetime import date
from decimal import Decimal

import pytest
from accounts.models import Project, UserProfile
from django.contrib.auth import get_user_model
from freezegun import freeze_time

from content.models import (
    Document,
    DocumentCollectionAccount,
    DocumentFolder,
    DocumentItem,
    IssuerProfile,
)
from content.services.collection_account_service import (
    issue_collection_account,
    mark_collection_account_cancelled,
)
from content.services.accounting_service import assign_project_to_documents
from content.services.generated_document_filing_service import (
    file_collection_account,
)
from content.services.document_type_utils import (
    get_collection_account_document_type,
)

pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def client_user():
    user = User.objects.create_user(
        username='filing-client@example.com',
        email='filing-client@example.com',
        first_name='Ana',
        last_name='Pérez',
    )
    UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
        company_name='Acme SAS',
        nit='900123456',
    )
    return user


@pytest.fixture
def project(client_user):
    return Project.objects.create(name='Portal Acme', client=client_user)


@pytest.fixture
def issuer():
    return IssuerProfile.objects.create(
        name='ProjectApp',
        legal_name='ProjectApp SAS',
        identification_number='901000000',
        email='billing@projectapp.co',
        public_number_prefix='PA',
    )


def make_account(*, client_user=None, project=None, concept='Desarrollo web'):
    document = Document.objects.create(
        title=f'Cuenta de cobro — {concept}',
        document_type=get_collection_account_document_type(),
        commercial_status=Document.CommercialStatus.DRAFT,
        client_user=client_user,
        project=project,
    )
    DocumentCollectionAccount.objects.create(
        document=document,
        billing_concept=concept,
        payment_term_days=8,
    )
    DocumentItem.objects.create(
        document=document,
        position=1,
        description=concept,
        quantity=Decimal('1'),
        unit_price=Decimal('100000'),
        line_total=Decimal('100000'),
    )
    return document


def folder_path(document):
    return [
        *(folder.name for folder in document.folder.get_ancestors()),
        document.folder.name,
    ]


@freeze_time('2026-08-14 15:00:00')
def test_issue_files_under_project_month(issuer, project, client_user):
    document = make_account(client_user=client_user, project=project)

    issue_collection_account(document, issuer=issuer)
    document.refresh_from_db()

    assert folder_path(document) == [
        'Proyectos',
        'Portal Acme',
        'Cuentas de cobro',
        '2026',
        '08 - Agosto',
    ]


@freeze_time('2026-08-14 15:00:00')
def test_issue_applies_account_title_convention(issuer, project, client_user):
    document = make_account(
        client_user=client_user,
        project=project,
        concept='Desarrollo del portal',
    )

    issue_collection_account(
        document,
        issuer=issuer,
        number_allocator=lambda: 'PA-ACME-007',
    )
    document.refresh_from_db()

    assert document.title == (
        '2026-08-14 · PA-ACME-007 · Desarrollo del portal'
    )


@freeze_time('2026-08-14 15:00:00')
def test_repeated_filing_reuses_hierarchy(issuer, project, client_user):
    document = make_account(client_user=client_user, project=project)
    issue_collection_account(document, issuer=issuer)
    initial_folder_count = DocumentFolder.objects.count()

    file_collection_account(document)
    file_collection_account(document)

    assert DocumentFolder.objects.count() == initial_folder_count


@freeze_time('2026-08-14 15:00:00')
def test_issue_without_project_uses_client_branch(issuer, client_user):
    document = make_account(client_user=client_user)

    issue_collection_account(document, issuer=issuer)
    document.refresh_from_db()

    assert folder_path(document) == [
        'Clientes',
        'Ana Pérez',
        'Sin proyecto',
        'Cuentas de cobro',
        '2026',
        '08 - Agosto',
    ]


@freeze_time('2026-08-14 15:00:00')
def test_cancelled_issue_moves_to_cancelled_branch(issuer, project, client_user):
    document = make_account(client_user=client_user, project=project)
    issue_collection_account(document, issuer=issuer)

    mark_collection_account_cancelled(document)
    document.refresh_from_db()

    assert folder_path(document)[-3:] == ['2026', '08 - Agosto', 'Anuladas']


def test_cancelled_draft_uses_unissued_branch(project, client_user):
    document = make_account(client_user=client_user, project=project)

    mark_collection_account_cancelled(document)
    document.refresh_from_db()

    assert folder_path(document)[-3:] == [
        'Cuentas de cobro', 'Sin emitir', 'Anuladas',
    ]


def test_assigning_project_keeps_unissued_draft_unfiled(project, client_user):
    document = make_account(client_user=client_user)

    assign_project_to_documents([document.pk], project, user=None)
    document.refresh_from_db()

    assert document.project_id == project.pk
    assert document.folder_id is None


@freeze_time('2026-09-01 02:00:00')
def test_issue_uses_bogota_calendar_date(issuer, project, client_user):
    document = make_account(client_user=client_user, project=project)

    issue_collection_account(document, issuer=issuer)
    document.refresh_from_db()

    assert document.issue_date == date(2026, 8, 31)
