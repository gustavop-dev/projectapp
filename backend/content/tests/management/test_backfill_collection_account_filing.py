from datetime import date
from io import StringIO

import pytest
from accounts.models import UserProfile
from django.contrib.auth import get_user_model
from django.core.management import call_command

from content.models import Document, DocumentCollectionAccount, DocumentFolder
from content.services.document_type_utils import (
    get_collection_account_document_type,
)

pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def client_user():
    user = User.objects.create_user(
        username='backfill-client@example.com',
        email='backfill-client@example.com',
        first_name='Mario',
        last_name='Rojas',
    )
    UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
        company_name='Rojas SAS',
        nit='900765432',
    )
    return user


def make_historical_account(client_user, *, folder=None, issue_date=date(2026, 7, 9)):
    document = Document.objects.create(
        title='Cuenta antigua',
        document_type=get_collection_account_document_type(),
        commercial_status=Document.CommercialStatus.ISSUED,
        client_user=client_user,
        issue_date=issue_date,
        public_number='PA-ROJAS-004',
        folder=folder,
    )
    DocumentCollectionAccount.objects.create(
        document=document,
        billing_concept='Mantenimiento mensual',
    )
    return document


def test_backfill_defaults_to_dry_run(client_user):
    document = make_historical_account(client_user)
    output = StringIO()

    call_command('backfill_collection_account_filing', stdout=output)
    document.refresh_from_db()

    assert document.folder_id is None
    assert not DocumentFolder.objects.filter(system_key__isnull=False).exists()
    assert 'WOULD FILE' in output.getvalue()


def test_backfill_apply_files_folderless_account(client_user):
    document = make_historical_account(client_user)

    call_command(
        'backfill_collection_account_filing',
        '--apply',
        stdout=StringIO(),
    )
    document.refresh_from_db()

    assert document.folder.name == '07 - Julio'
    assert document.title == (
        '2026-07-09 · PA-ROJAS-004 · Mantenimiento mensual'
    )


def test_backfill_preserves_manual_folder(client_user):
    manual = DocumentFolder.objects.create(name='Archivo especial')
    document = make_historical_account(client_user, folder=manual)

    call_command(
        'backfill_collection_account_filing',
        '--apply',
        stdout=StringIO(),
    )
    document.refresh_from_db()

    assert document.folder_id == manual.pk


def test_backfill_skips_missing_issue_date(client_user):
    document = make_historical_account(client_user, issue_date=None)
    output = StringIO()

    call_command(
        'backfill_collection_account_filing',
        '--apply',
        stdout=output,
    )
    document.refresh_from_db()

    assert document.folder_id is None
    assert 'sin fecha de emisión' in output.getvalue()
