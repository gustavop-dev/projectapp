"""Tests for collection_account_service business rules."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from freezegun import freeze_time

from accounts.models import Project, UserProfile
from content.models import Document, DocumentCollectionAccount, DocumentItem, IssuerProfile
from content.services.collection_account_service import (
    CollectionAccountError,
    allocate_public_number,
    assert_draft_for_mutation,
    commercial_is_overdue,
    is_collection_account,
    issue_collection_account,
    mark_collection_account_cancelled,
    mark_collection_account_paid,
    recalculate_document_totals,
)
from content.services.document_type_codes import COLLECTION_ACCOUNT
from content.services.document_type_utils import (
    get_collection_account_document_type,
    get_markdown_document_type,
)

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def issuer():
    return IssuerProfile.objects.create(
        name='Issuer Co',
        legal_name='Issuer LLC',
        identification_number='900',
        email='issuer@example.com',
        phone='+5700',
        address='Addr',
        public_number_prefix='ZZ',
    )


@pytest.fixture
def admin_actor():
    user = User.objects.create_user(
        username='svc-admin@test.com',
        email='svc-admin@test.com',
        password='pass12345',
    )
    UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_ADMIN,
        is_onboarded=True,
        profile_completed=True,
    )
    return user


@pytest.fixture
def client_user(admin_actor):
    user = User.objects.create_user(
        username='svc-client@test.com',
        email='svc-client@test.com',
        password='pass12345',
        first_name='Pat',
        last_name='Lee',
    )
    UserProfile.objects.create(
        user=user,
        role=UserProfile.ROLE_CLIENT,
        is_onboarded=True,
        profile_completed=True,
        company_name='ClientCo',
        cedula='123',
        created_by=admin_actor,
    )
    return user


@pytest.fixture
def project(client_user):
    return Project.objects.create(
        name='Svc Project',
        client=client_user,
        status=Project.STATUS_ACTIVE,
        progress=0,
    )


def _ca_document(**kwargs):
    dt = get_collection_account_document_type()
    defaults = {
        'title': 'CA',
        'document_type': dt,
        'commercial_status': Document.CommercialStatus.DRAFT,
        'total': Decimal('0'),
    }
    defaults.update(kwargs)
    return Document.objects.create(**defaults)


def test_commercial_is_overdue_returns_false_for_non_collection_account_document():
    md = get_markdown_document_type()
    doc = Document.objects.create(
        title='Md',
        document_type=md,
        commercial_status=Document.CommercialStatus.ISSUED,
        due_date=timezone.now().date(),
    )

    assert commercial_is_overdue(doc) is False


def test_commercial_is_overdue_returns_false_when_status_is_draft():
    doc = _ca_document(commercial_status=Document.CommercialStatus.DRAFT)
    DocumentCollectionAccount.objects.create(document=doc)
    doc.due_date = timezone.now().date()
    doc.save(update_fields=['due_date'])

    assert commercial_is_overdue(doc) is False


def test_commercial_is_overdue_returns_false_when_due_date_is_missing():
    doc = _ca_document(commercial_status=Document.CommercialStatus.ISSUED)
    DocumentCollectionAccount.objects.create(document=doc)

    assert commercial_is_overdue(doc) is False


def test_commercial_is_overdue_returns_false_when_due_date_string_is_unparseable():
    stub = SimpleNamespace(
        document_type=SimpleNamespace(code=COLLECTION_ACCOUNT),
        commercial_status=Document.CommercialStatus.ISSUED,
        due_date='not-a-real-date',
    )

    assert commercial_is_overdue(stub) is False


def test_commercial_is_overdue_returns_false_when_parse_date_returns_none():
    stub = SimpleNamespace(
        document_type=SimpleNamespace(code=COLLECTION_ACCOUNT),
        commercial_status=Document.CommercialStatus.ISSUED,
        due_date='99-99-99',
    )

    assert commercial_is_overdue(stub) is False


def test_commercial_is_overdue_returns_false_when_due_date_string_is_in_future():
    stub = SimpleNamespace(
        document_type=SimpleNamespace(code=COLLECTION_ACCOUNT),
        commercial_status=Document.CommercialStatus.ISSUED,
        due_date='2099-01-01',
    )

    assert commercial_is_overdue(stub) is False


def test_recalculate_document_totals_sets_zero_totals_when_no_line_items():
    doc = _ca_document(discount_total=Decimal('5'))

    recalculate_document_totals(doc)

    assert doc.subtotal == Decimal('0')
    assert doc.tax_total == Decimal('0')
    assert doc.total == Decimal('-5')


def test_recalculate_document_totals_aggregates_line_items():
    doc = _ca_document(discount_total=Decimal('0'))
    DocumentItem.objects.create(
        document=doc,
        position=0,
        description='A',
        quantity=Decimal('2'),
        unit_price=Decimal('50'),
        discount_amount=Decimal('10'),
        tax_amount=Decimal('5'),
        line_total=Decimal('95'),
    )

    recalculate_document_totals(doc)

    assert doc.subtotal == Decimal('90')
    assert doc.tax_total == Decimal('5')
    assert doc.total == Decimal('95')


def test_allocate_public_number_increments_per_issuer_and_year(issuer):
    n1 = allocate_public_number(issuer)
    n2 = allocate_public_number(issuer)

    assert n1.startswith('ZZ-')
    assert n2.startswith('ZZ-')
    assert n1 != n2


def test_allocate_public_number_uses_pa_prefix_when_prefix_is_blank():
    bare = IssuerProfile.objects.create(name='Bare Issuer', public_number_prefix='')

    num = allocate_public_number(bare)

    assert num.split('-')[0] == 'PA'


def test_issue_collection_account_raises_when_document_is_not_collection_type(issuer, project, client_user):
    md = get_markdown_document_type()
    doc = Document.objects.create(
        title='Wrong',
        document_type=md,
        commercial_status=Document.CommercialStatus.DRAFT,
        project=project,
        client_user=client_user,
    )

    with pytest.raises(CollectionAccountError, match='not a collection account'):
        issue_collection_account(doc, issuer=issuer)


def test_issue_collection_account_raises_when_status_is_not_draft(issuer, project, client_user):
    doc = _ca_document(
        commercial_status=Document.CommercialStatus.ISSUED,
        project=project,
        client_user=client_user,
    )
    DocumentCollectionAccount.objects.create(document=doc)

    with pytest.raises(CollectionAccountError, match='Only draft'):
        issue_collection_account(doc, issuer=issuer)


def test_issue_collection_account_raises_when_no_client_can_be_resolved(issuer):
    doc = _ca_document()
    DocumentCollectionAccount.objects.create(document=doc)

    with pytest.raises(CollectionAccountError, match='client_user or project'):
        issue_collection_account(doc, issuer=issuer)


def test_issue_collection_account_raises_for_fixed_date_without_due_date(issuer, project, client_user):
    doc = _ca_document(project=project, client_user=client_user)
    DocumentCollectionAccount.objects.create(
        document=doc,
        payment_term_type=DocumentCollectionAccount.PaymentTermType.FIXED_DATE,
    )

    with pytest.raises(CollectionAccountError, match='due_date is required'):
        issue_collection_account(doc, issuer=issuer)


def test_issue_collection_account_preserves_due_date_for_fixed_date_term(issuer, project, client_user):
    doc = _ca_document(
        project=project,
        client_user=client_user,
        due_date=date(2026, 12, 31),
    )
    DocumentCollectionAccount.objects.create(
        document=doc,
        payment_term_type=DocumentCollectionAccount.PaymentTermType.FIXED_DATE,
    )

    issue_collection_account(doc, issuer=issuer)
    doc.refresh_from_db()

    assert doc.due_date.isoformat() == '2026-12-31'


@freeze_time('2026-04-01')
def test_issue_collection_account_sets_due_from_payment_term_days_after_issue(issuer, project, client_user):
    doc = _ca_document(project=project, client_user=client_user)
    DocumentCollectionAccount.objects.create(
        document=doc,
        payment_term_type=DocumentCollectionAccount.PaymentTermType.DAYS_AFTER_ISSUE,
        payment_term_days=7,
    )

    issue_collection_account(doc, issuer=issuer)
    doc.refresh_from_db()

    assert doc.due_date.isoformat() == '2026-04-08'


@freeze_time('2026-05-10')
def test_issue_collection_account_sets_due_today_for_non_fixed_non_days_term_when_missing(
    issuer, project, client_user,
):
    doc = _ca_document(project=project, client_user=client_user)
    DocumentCollectionAccount.objects.create(
        document=doc,
        payment_term_type=DocumentCollectionAccount.PaymentTermType.AGAINST_DELIVERY,
    )

    issue_collection_account(doc, issuer=issuer)
    doc.refresh_from_db()

    assert doc.due_date.isoformat() == '2026-05-10'


def test_mark_collection_account_paid_returns_document_when_already_paid(issuer, project, client_user):
    doc = _ca_document(
        commercial_status=Document.CommercialStatus.PAID,
        project=project,
        client_user=client_user,
    )
    DocumentCollectionAccount.objects.create(document=doc)

    out = mark_collection_account_paid(doc)

    assert out.pk == doc.pk


def test_mark_collection_account_paid_raises_when_document_is_not_issued(project, client_user):
    doc = _ca_document(
        commercial_status=Document.CommercialStatus.DRAFT,
        project=project,
        client_user=client_user,
    )
    DocumentCollectionAccount.objects.create(document=doc)

    with pytest.raises(CollectionAccountError, match='Only issued'):
        mark_collection_account_paid(doc)


def test_mark_collection_account_paid_raises_when_document_is_not_collection_type(project, client_user):
    md = get_markdown_document_type()
    doc = Document.objects.create(
        title='X',
        document_type=md,
        commercial_status=Document.CommercialStatus.ISSUED,
        project=project,
        client_user=client_user,
    )

    with pytest.raises(CollectionAccountError, match='not a collection account'):
        mark_collection_account_paid(doc)


def test_mark_collection_account_paid_sets_paid_when_document_is_issued(admin_actor, project, client_user):
    doc = _ca_document(
        commercial_status=Document.CommercialStatus.ISSUED,
        project=project,
        client_user=client_user,
    )
    DocumentCollectionAccount.objects.create(document=doc)

    mark_collection_account_paid(doc, acting_user=admin_actor)
    doc.refresh_from_db()

    assert doc.commercial_status == Document.CommercialStatus.PAID


def test_mark_collection_account_cancelled_returns_document_when_already_cancelled(
    issuer, project, client_user,
):
    doc = _ca_document(
        commercial_status=Document.CommercialStatus.CANCELLED,
        project=project,
        client_user=client_user,
    )
    DocumentCollectionAccount.objects.create(document=doc)

    out = mark_collection_account_cancelled(doc)

    assert out.pk == doc.pk


def test_mark_collection_account_cancelled_raises_when_document_is_paid(issuer, project, client_user):
    doc = _ca_document(
        commercial_status=Document.CommercialStatus.PAID,
        project=project,
        client_user=client_user,
    )
    DocumentCollectionAccount.objects.create(document=doc)

    with pytest.raises(CollectionAccountError, match='Paid documents cannot'):
        mark_collection_account_cancelled(doc)


def test_mark_collection_account_cancelled_raises_when_document_is_not_collection_type(project, client_user):
    md = get_markdown_document_type()
    doc = Document.objects.create(
        title='X',
        document_type=md,
        commercial_status=Document.CommercialStatus.DRAFT,
        project=project,
        client_user=client_user,
    )

    with pytest.raises(CollectionAccountError, match='not a collection account'):
        mark_collection_account_cancelled(doc)


def test_mark_collection_account_cancelled_sets_cancelled_when_document_is_issued(
    admin_actor, project, client_user,
):
    doc = _ca_document(
        commercial_status=Document.CommercialStatus.ISSUED,
        project=project,
        client_user=client_user,
    )
    DocumentCollectionAccount.objects.create(document=doc)

    mark_collection_account_cancelled(doc, acting_user=admin_actor)
    doc.refresh_from_db()

    assert doc.commercial_status == Document.CommercialStatus.CANCELLED


def test_mark_collection_account_cancelled_raises_for_unsupported_commercial_status(
    issuer, project, client_user,
):
    doc = _ca_document(
        commercial_status=None,
        project=project,
        client_user=client_user,
    )
    DocumentCollectionAccount.objects.create(document=doc)

    with pytest.raises(CollectionAccountError, match='Only draft or issued'):
        mark_collection_account_cancelled(doc)


def test_assert_draft_for_mutation_raises_when_document_is_not_collection_account(project, client_user):
    md = get_markdown_document_type()
    doc = Document.objects.create(
        title='X',
        document_type=md,
        commercial_status=Document.CommercialStatus.DRAFT,
        project=project,
        client_user=client_user,
    )

    with pytest.raises(CollectionAccountError, match='not a collection account'):
        assert_draft_for_mutation(doc)


def test_assert_draft_for_mutation_raises_when_document_is_not_draft(project, client_user):
    doc = _ca_document(
        commercial_status=Document.CommercialStatus.ISSUED,
        project=project,
        client_user=client_user,
    )
    DocumentCollectionAccount.objects.create(document=doc)

    with pytest.raises(CollectionAccountError, match='Only draft collection accounts'):
        assert_draft_for_mutation(doc)


def test_assert_draft_for_mutation_succeeds_for_draft_collection_account(project, client_user):
    doc = _ca_document(
        commercial_status=Document.CommercialStatus.DRAFT,
        project=project,
        client_user=client_user,
    )
    DocumentCollectionAccount.objects.create(document=doc)

    assert_draft_for_mutation(doc)


def test_is_collection_account_returns_true_for_collection_document_type():
    doc = _ca_document()

    assert is_collection_account(doc) is True


def test_issue_collection_account_uses_project_client_when_client_user_not_set(issuer, project, client_user):
    doc = _ca_document(project=project, client_user=None)
    DocumentCollectionAccount.objects.create(document=doc)

    issue_collection_account(doc, issuer=issuer)
    doc.refresh_from_db()
    ext = doc.collection_account

    assert ext.customer_email == client_user.email


def test_issue_collection_account_uses_person_name_when_user_has_no_profile(
    issuer, admin_actor,
):
    user = User.objects.create_user(
        username='svc-person@test.com',
        email='svc-person@test.com',
        password='pass12345',
        first_name='Sam',
        last_name='Rivera',
    )
    project_local = Project.objects.create(
        name='Personal Project',
        client=user,
        status=Project.STATUS_ACTIVE,
        progress=0,
    )
    doc = _ca_document(project=project_local, client_user=user)
    DocumentCollectionAccount.objects.create(document=doc)

    issue_collection_account(doc, issuer=issuer, acting_user=admin_actor)
    ext = DocumentCollectionAccount.objects.get(document=doc)

    assert ext.customer_name == 'Sam Rivera'
    assert ext.customer_contact_name == 'Sam Rivera'
