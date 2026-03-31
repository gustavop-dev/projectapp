"""
Business rules for collection account documents: numbering, totals, lifecycle transitions.
"""
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.utils.dateparse import parse_date

from content.models import Document, DocumentCollectionAccount, DocumentNumberSequence
from content.services.document_type_codes import COLLECTION_ACCOUNT


class CollectionAccountError(Exception):
    """Invalid state or input for collection account operations."""


def is_collection_account(document):
    dt = document.document_type
    return dt is not None and dt.code == COLLECTION_ACCOUNT


def commercial_is_overdue(document):
    """
    Derived overdue: issued, past due_date, not paid or cancelled.
    """
    if not is_collection_account(document):
        return False
    if document.commercial_status != Document.CommercialStatus.ISSUED:
        return False
    due = document.due_date
    if not due:
        return False
    if isinstance(due, str):
        due = parse_date(due)
        if due is None:
            return False
    return due < timezone.now().date()


def recalculate_document_totals(document):
    """Aggregate line items into document money fields."""
    lines = list(document.items.all())
    if not lines:
        document.subtotal = Decimal('0')
        document.tax_total = Decimal('0')
        document.total = Decimal('0') - document.discount_total
        return

    subtotal = sum(
        (li.quantity * li.unit_price - li.discount_amount for li in lines),
        Decimal('0'),
    )
    tax_total = sum((li.tax_amount for li in lines), Decimal('0'))
    line_sum = sum((li.line_total for li in lines), Decimal('0'))
    document.subtotal = subtotal
    document.tax_total = tax_total
    document.total = line_sum - document.discount_total


@transaction.atomic
def allocate_public_number(issuer):
    """Thread-safe next public_number for issuer and current UTC year."""
    year = timezone.now().year
    seq, _ = DocumentNumberSequence.objects.select_for_update().get_or_create(
        issuer=issuer,
        year=year,
        defaults={'last_value': 0},
    )
    DocumentNumberSequence.objects.filter(pk=seq.pk).update(last_value=F('last_value') + 1)
    seq.refresh_from_db()
    prefix = (issuer.public_number_prefix or 'PA').strip() or 'PA'
    return f'{prefix}-{year}-{seq.last_value:04d}'


def _resolve_client_user(document):
    if document.client_user_id:
        return document.client_user
    if document.project_id:
        return document.project.client
    return None


def _fill_payer_from_issuer(extension, issuer):
    extension.payer_name = issuer.legal_name or issuer.name
    extension.payer_identification = issuer.identification_number
    extension.payer_identification_type = issuer.identification_type
    extension.payer_address = issuer.address
    extension.payer_phone = issuer.phone
    extension.payer_email = issuer.email or ''


def _fill_customer_from_user(extension, user):
    from accounts.models import UserProfile

    profile = getattr(user, 'profile', None)
    name = ''
    if profile and profile.company_name:
        name = profile.company_name
    else:
        name = f'{user.first_name} {user.last_name}'.strip() or user.email
    extension.customer_name = name
    extension.customer_email = user.email or ''
    if profile:
        extension.customer_identification = profile.cedula or ''
    extension.customer_contact_name = f'{user.first_name} {user.last_name}'.strip()
    extension.customer_identification_type = ''


@transaction.atomic
def issue_collection_account(document, *, issuer, acting_user=None):
    """
    Transition draft -> issued: allocate public number, set dates, snapshot payer/customer.
    """
    if not is_collection_account(document):
        raise CollectionAccountError('Document is not a collection account.')
    if document.commercial_status != Document.CommercialStatus.DRAFT:
        raise CollectionAccountError('Only draft documents can be issued.')

    ext, _ = DocumentCollectionAccount.objects.get_or_create(document=document)

    _fill_payer_from_issuer(ext, issuer)

    client_user = _resolve_client_user(document)
    if not client_user:
        raise CollectionAccountError('client_user or project with client is required to issue.')
    _fill_customer_from_user(ext, client_user)

    today = timezone.now().date()
    document.issue_date = today
    document.issuer = issuer
    document.public_number = allocate_public_number(issuer)

    ptt = ext.payment_term_type
    if ptt == DocumentCollectionAccount.PaymentTermType.DAYS_AFTER_ISSUE:
        days = ext.payment_term_days or 0
        document.due_date = today + timedelta(days=days)
    elif ptt == DocumentCollectionAccount.PaymentTermType.FIXED_DATE:
        if not document.due_date:
            raise CollectionAccountError('due_date is required for fixed_date payment term.')
    else:
        if not document.due_date:
            document.due_date = today

    recalculate_document_totals(document)
    document.commercial_status = Document.CommercialStatus.ISSUED
    document.updated_by = acting_user
    document.save()
    ext.save()

    return document


@transaction.atomic
def mark_collection_account_paid(document, *, acting_user=None):
    if not is_collection_account(document):
        raise CollectionAccountError('Document is not a collection account.')
    if document.commercial_status == Document.CommercialStatus.PAID:
        return document
    if document.commercial_status != Document.CommercialStatus.ISSUED:
        raise CollectionAccountError('Only issued accounts can be marked paid.')
    document.commercial_status = Document.CommercialStatus.PAID
    document.updated_by = acting_user
    document.save(update_fields=['commercial_status', 'updated_by', 'updated_at'])
    return document


@transaction.atomic
def mark_collection_account_cancelled(document, *, acting_user=None):
    if not is_collection_account(document):
        raise CollectionAccountError('Document is not a collection account.')
    if document.commercial_status == Document.CommercialStatus.CANCELLED:
        return document
    if document.commercial_status == Document.CommercialStatus.PAID:
        raise CollectionAccountError('Paid documents cannot be cancelled.')
    if document.commercial_status not in (
        Document.CommercialStatus.DRAFT,
        Document.CommercialStatus.ISSUED,
    ):
        raise CollectionAccountError('Only draft or issued accounts can be cancelled.')
    document.commercial_status = Document.CommercialStatus.CANCELLED
    document.updated_by = acting_user
    document.save(update_fields=['commercial_status', 'updated_by', 'updated_at'])
    return document


def assert_draft_for_mutation(document):
    if not is_collection_account(document):
        raise CollectionAccountError('Document is not a collection account.')
    if document.commercial_status != Document.CommercialStatus.DRAFT:
        raise CollectionAccountError('Only draft collection accounts can be edited.')
