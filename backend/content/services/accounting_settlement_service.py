"""Settling an expected income that was collected short.

A client pays through Wompi, a bank or a withholding agent, and what lands is
4-10% below what was invoiced. That gap is not an unpaid balance — nobody will
ever collect it — yet the plain "Liquidar" action leaves it open forever,
because the pending amount is derived from the expected total minus its liquid
children.

This service closes the loop in one atomic operation: it registers what was
received and resolves the rest — deductions become linked expenses that count
as payment credit against the GROSS expected total, follow-ups move their
amount into their own expected record. The arithmetic that governs everything:

    pending = total - already_paid          # paid = liquid children + linked deductions
    received + deductions + follow_ups + unassigned = pending
    new parent total = total - follow_ups   # deductions keep the income gross

The income stays gross so the deduction can reduce utility as a real expense
without double-counting (the liquid total alone no longer carries the loss).
With no allocations the parent is untouched and the behaviour is identical to
today's liquidation. Whatever is left unassigned simply stays pending, so a
user who does not want to decide yet is never forced to.

``received`` may be zero when deductions and follow-ups cover the whole
pending: nothing was collected, so no liquid child is created and nobody is
notified — the settlement is pure bookkeeping that closes the residual.

The codebase already prescribed this workflow manually — see the error raised
when writing off a partially collected record in
``IncomeRecordCreateUpdateSerializer.validate``: *"Reduce su monto y registra la
diferencia como un ingreso perdido aparte"*.
"""
from decimal import ROUND_DOWN, Decimal

from django.db import transaction
from django.db.models import Sum

from content.models import AccountingChangeLog, Document, ExpenseRecord, IncomeRecord
from content.serializers.accounting import (
    ExpenseRecordCreateUpdateSerializer,
    IncomeRecordCreateUpdateSerializer,
    payment_status_for,
    split_half,
)
from content.services import accounting_service

EntityType = AccountingChangeLog.EntityType

TWO_PLACES = Decimal('0.01')


def _paid_total(income):
    """Liquid children plus linked deductions fulfilling this expected record.

    The `kind=LIQUID` filter is load-bearing: `limit_choices_to` constrains the
    FK's target, not its source, so a lost record may point at an expected
    parent and must never count as payment. Deductions count as credit because
    the income keeps its gross total — the fee was applied at origin, so that
    part of the total will never arrive as a liquid child. The
    `deduction_type` exclude mirrors the LIQUID guard: only real deductions
    may credit the parent.
    """
    liquid = income.liquid_records.filter(
        kind=IncomeRecord.Kind.LIQUID,
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    deducted = income.deduction_records.exclude(
        deduction_type='',
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    return liquid + deducted


def income_payment_status(income):
    """Derived collection state ('pending'/'partial'/'paid') for an expected income.

    Single owner of the "is it fully paid" question outside serializers:
    the settle→cuenta sync below and the panel mark-paid guard both use it.
    """
    return payment_status_for(_paid_total(income), income.total_amount)


def _sync_linked_collection_accounts(income, user):
    """Fully paid income → its linked issued cuenta de cobro becomes paid.

    Runs inside settle's transaction. Idempotent by construction: only
    ISSUED documents are touched, so drafts stay drafts, cancelled stay
    cancelled and an already-paid cuenta is never revisited.
    """
    if income_payment_status(income) != 'paid':
        return
    from content.services.collection_account_service import (
        mark_collection_account_paid,
    )

    linked = income.collection_documents.filter(
        commercial_status=Document.CommercialStatus.ISSUED,
    )
    for document in linked:
        mark_collection_account_paid(document, acting_user=user)


def _proportional_split(parent, amount):
    """Partner amounts keeping the parent's ratio, never exceeding `amount`.

    Both partners are rounded down independently so the unassigned residue
    (the company share) keeps its own proportion instead of being absorbed by
    whoever is computed last.
    """
    total = parent.total_amount or Decimal('0')
    if not total:
        return split_half(amount)
    gustavo = (amount * parent.gustavo_amount / total).quantize(
        TWO_PLACES, rounding=ROUND_DOWN,
    )
    carlos = (amount * parent.carlos_amount / total).quantize(
        TWO_PLACES, rounding=ROUND_DOWN,
    )
    return gustavo, carlos


def _deduction_label(deduction):
    """Free text wins for 'Otro'; otherwise the choice's Spanish label."""
    if deduction['type'] == ExpenseRecord.DeductionType.OTHER:
        return deduction.get('detail', '').strip() or 'Otro'
    return ExpenseRecord.DeductionType(deduction['type']).label


def _stamp_source_ref(records, income_id):
    """Trace every record back to the settlement that produced it.

    `source_ref` is not a serializer field, so it is written afterwards with a
    queryset update; the in-memory instances are patched too because they are
    what the view serializes back.
    """
    if not records:
        return
    source_ref = f'income:{income_id}:settlement'
    type(records[0]).objects.filter(
        pk__in=[record.pk for record in records],
    ).update(source_ref=source_ref)
    for record in records:
        record.source_ref = source_ref


@transaction.atomic
def settle_expected_income(income, data, user):
    """Register a payment and resolve its shortfall in one operation.

    `data` comes from a validated ``IncomeSettlementSerializer``. Raises
    ``ValueError`` with a Spanish message on any business-rule breach; the
    view turns it into a 400.
    """
    if income.kind != IncomeRecord.Kind.EXPECTED:
        raise ValueError('Solo se puede liquidar un ingreso esperado.')

    deductions = data.get('deductions') or []
    follow_ups = data.get('expected_incomes') or []
    received = data['total_amount']
    deducted = sum((d['amount'] for d in deductions), Decimal('0'))
    reexpected = sum((e['amount'] for e in follow_ups), Decimal('0'))

    pending = income.total_amount - _paid_total(income)
    if pending <= 0:
        raise ValueError('Este ingreso esperado ya está completamente pagado.')
    if received <= 0 and not (deducted or reexpected):
        raise ValueError('El monto recibido debe ser mayor a cero.')
    if received + deducted + reexpected > pending:
        raise ValueError(
            'La suma del monto recibido, los gastos y los nuevos ingresos '
            'esperados no puede superar el saldo pendiente '
            f'(${pending:,.2f}).'
        )

    liquid = _create_liquid_child(income, data, user) if received > 0 else None
    expenses = [
        _create_deduction(income, data, deduction, user)
        for deduction in deductions
    ]
    new_expected = [
        _create_follow_up(income, follow_up, user) for follow_up in follow_ups
    ]

    # Only follow-ups shrink the parent: their amount now lives in its own
    # expected record. Deductions keep the income gross — they count as
    # payment credit via the source_income link instead.
    if reexpected:
        _reduce_parent(income, income.total_amount - reexpected, user)

    _stamp_source_ref(expenses, income.pk)
    _stamp_source_ref(new_expected, income.pk)

    income.refresh_from_db()
    _sync_linked_collection_accounts(income, user)
    return {
        'income': income,
        'liquid': liquid,
        'expenses': expenses,
        'expected_incomes': new_expected,
    }


def _create_liquid_child(income, data, user):
    """The payment itself — the only record that notifies, as it does today."""
    payload = {
        'concept': data['concept'],
        'kind': IncomeRecord.Kind.LIQUID,
        'period_date': data['period_date'],
        'destination': data['destination'],
        'ledger': income.ledger,
        'total_amount': data['total_amount'],
        'expected_income': income.pk,
        # Inherited from the projection: without this the collected money
        # would drop out of its client's totals the moment it is settled.
        'client': income.client_id,
        # Same inheritance for the project — a liquid with no project would
        # split the deal across two per-project buckets (PA-51).
        'project': income.project_id,
        'origin': income.origin,
        'notes': data.get('notes', ''),
    }
    if data.get('gustavo_amount') is not None:
        payload['gustavo_amount'] = data['gustavo_amount']
    if data.get('carlos_amount') is not None:
        payload['carlos_amount'] = data['carlos_amount']
    # The child copies the parent's origin rather than classifying anything, so
    # it may be as blank as the parent — most of the book predates the field,
    # and refusing to settle those would be a far worse answer than a liquid
    # that is exactly as unclassified as what it collects.
    serializer = IncomeRecordCreateUpdateSerializer(
        data=payload, context={'settlement': True},
    )
    serializer.is_valid(raise_exception=True)
    return accounting_service.create_record(
        EntityType.INCOME, serializer, user,
    )


def _create_deduction(income, data, deduction, user):
    """The shortfall as an expense — never a pocket movement.

    `register_in_pocket=False` is load-bearing: this money never entered the
    pocket, it was discounted before the transfer ever arrived.
    """
    label = _deduction_label(deduction)
    gustavo, carlos = _proportional_split(income, deduction['amount'])
    serializer = ExpenseRecordCreateUpdateSerializer(
        data={
            'concept': f'{label} — {income.concept}'[:255],
            'period_date': data['period_date'],
            'category': ExpenseRecord.Category.BUSINESS,
            'ledger': income.ledger,
            'total_amount': deduction['amount'],
            'gustavo_amount': gustavo,
            'carlos_amount': carlos,
            'deduction_type': deduction['type'],
            'register_in_pocket': False,
            'notes': data.get('notes', ''),
        },
        # The write serializer rejects deduction_type outside this flow.
        context={'settlement': True},
    )
    serializer.is_valid(raise_exception=True)
    expense = accounting_service.create_record(
        EntityType.EXPENSE, serializer, user, notify=False,
    )
    # Not serializer-writable — stamped afterwards like source_ref. This link
    # is what credits the deduction against the parent's gross total.
    ExpenseRecord.objects.filter(pk=expense.pk).update(source_income=income)
    expense.source_income = income
    return expense


def _create_follow_up(income, follow_up, user):
    """A balance that WILL be collected, rescheduled as its own expected."""
    gustavo, carlos = _proportional_split(income, follow_up['amount'])
    serializer = IncomeRecordCreateUpdateSerializer(
        data={
            'concept': follow_up['concept'],
            'kind': IncomeRecord.Kind.EXPECTED,
            'period_date': follow_up['period_date'],
            'destination': income.destination,
            'ledger': income.ledger,
            'total_amount': follow_up['amount'],
            'gustavo_amount': gustavo,
            'carlos_amount': carlos,
            'client': income.client_id,
            'origin': income.origin,
        },
        # Same as the liquid child: the rescheduled balance inherits the
        # parent's line of business, blank included.
        context={'settlement': True},
    )
    serializer.is_valid(raise_exception=True)
    return accounting_service.create_record(
        EntityType.INCOME, serializer, user, notify=False,
    )


def _reduce_parent(income, new_total, user):
    """Shrink the expected record by whatever was moved out of it.

    The split must be rescaled in the same call: `PartnerSplitMixin` rejects
    partner amounts adding up to more than the total, and the old split still
    reflects the old (larger) total.
    """
    gustavo, carlos = _proportional_split(income, new_total)
    serializer = IncomeRecordCreateUpdateSerializer(
        instance=income,
        data={
            'total_amount': new_total,
            'gustavo_amount': gustavo,
            'carlos_amount': carlos,
        },
        partial=True,
    )
    serializer.is_valid(raise_exception=True)
    return accounting_service.update_record(
        EntityType.INCOME, income, serializer, user, notify=False,
    )
