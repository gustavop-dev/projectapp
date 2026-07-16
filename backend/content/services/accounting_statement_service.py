"""Credit-card statement orchestration (extractos).

Analytical ledger only: statements and their transactions NEVER create
ExpenseRecords or PocketMovements — per the operating model, expenses leave
the pocket and only the card payment (abono) is registered in the main
ledgers.

Audit shape: statement-level changes go through the regular pipeline and
email (accounting_service); transaction and alias changes are audited
WITHOUT their own email — same precedent as auto pocket movements — so a
40-line statement doesn't fire 40 notifications.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

from django.db import transaction
from django.db.models import Sum

from content.models import (
    CreditCard,
    CreditCardStatement,
    MerchantAlias,
    TransactionCategory,
    normalize_descriptor,
)
from content.serializers.accounting import month_label
from content.utils import today_bogota
from content.services import accounting_service
from content.services.accounting_service import (
    TRACKED_FIELDS,
    Action,
    EntityType,
    compute_changes,
    log_accounting_change,
    object_repr,
    snapshot_values,
)

# ±1 COP absorbs bank rounding on the purchases total; anything larger
# blocks finalize unless the owner explicitly forces it.
STATEMENT_TOTAL_TOLERANCE = Decimal('1.00')

Status = CreditCardStatement.Status


# ── Internal audit helpers (silent: no email) ──

def _log_silent(entity_type, instance, action, changes, user):
    log_accounting_change(
        entity_type=entity_type,
        object_id=instance.pk,
        object_repr=object_repr(entity_type, instance),
        action=action,
        changes=changes,
        actor=user,
    )


def _ensure_draft(statement):
    if statement.status != Status.DRAFT:
        raise ValueError(
            'El extracto ya está procesado. Reábrelo antes de modificar '
            'sus transacciones.'
        )


def _apply_alias(tx):
    """Fill merchant/category from a learned alias when the row has none.

    Gateway aliases never auto-apply: the descriptor hides the real
    merchant, so the mapping is only a hint for manual review.
    """
    if tx.merchant_name:
        return
    alias = MerchantAlias.objects.filter(
        match_text=normalize_descriptor(tx.raw_description),
        is_gateway=False,
    ).first()
    if alias is not None:
        tx.merchant_name = alias.merchant_name
        tx.category = alias.default_category
        tx.is_identified = True


# ── Statement lifecycle ──

@transaction.atomic
def create_statement_with_transactions(
    statement_serializer, transactions_serializer, user,
):
    """Create a DRAFT statement plus all its transactions atomically.

    One statement change log (with email) + one silent audit row per
    transaction. Known merchant aliases are applied to rows that arrive
    without a merchant.
    """
    statement = statement_serializer.save(created_by=user)
    transactions = transactions_serializer.save(
        statement=statement,
        created_by=user if getattr(user, 'is_authenticated', False) else None,
    )
    for tx in transactions:
        _apply_alias(tx)
        tx.save()
        _log_silent(
            EntityType.STATEMENT_TX, tx, Action.CREATED,
            compute_changes(
                EntityType.STATEMENT_TX, {},
                snapshot_values(tx, EntityType.STATEMENT_TX),
            ),
            user,
        )
    change_log = log_accounting_change(
        entity_type=EntityType.STATEMENT,
        object_id=statement.pk,
        object_repr=object_repr(EntityType.STATEMENT, statement),
        action=Action.CREATED,
        changes=compute_changes(
            EntityType.STATEMENT, {},
            snapshot_values(statement, EntityType.STATEMENT),
        ),
        actor=user,
    )
    accounting_service._notify(change_log)
    return statement


@transaction.atomic
def add_transactions(statement, transactions_serializer, user):
    """Batch-append transactions to a DRAFT statement (silent audit)."""
    _ensure_draft(statement)
    transactions = transactions_serializer.save(
        statement=statement,
        created_by=user if getattr(user, 'is_authenticated', False) else None,
    )
    for tx in transactions:
        _apply_alias(tx)
        tx.save()
        _log_silent(
            EntityType.STATEMENT_TX, tx, Action.CREATED,
            compute_changes(
                EntityType.STATEMENT_TX, {},
                snapshot_values(tx, EntityType.STATEMENT_TX),
            ),
            user,
        )
    return transactions


def update_transaction(tx, serializer, user):
    """Apply a validated partial update to one transaction (silent audit)."""
    _ensure_draft(tx.statement)
    old_values = snapshot_values(tx, EntityType.STATEMENT_TX)
    tx = serializer.save()
    changes = compute_changes(
        EntityType.STATEMENT_TX, old_values,
        snapshot_values(tx, EntityType.STATEMENT_TX),
    )
    if changes:
        _log_silent(EntityType.STATEMENT_TX, tx, Action.UPDATED, changes, user)
    return tx


def delete_transaction(tx, user):
    """Delete one transaction of a DRAFT statement (silent audit)."""
    _ensure_draft(tx.statement)
    old_values = snapshot_values(tx, EntityType.STATEMENT_TX)
    deleted_id = tx.pk
    deleted_repr = object_repr(EntityType.STATEMENT_TX, tx)
    changes = [
        {'field': field, 'label': label,
         'old': old_values.get(field, ''), 'new': ''}
        for field, label in TRACKED_FIELDS[EntityType.STATEMENT_TX]
        if old_values.get(field, '') != ''
    ]
    tx.delete()
    log_accounting_change(
        entity_type=EntityType.STATEMENT_TX,
        object_id=deleted_id,
        object_repr=deleted_repr,
        action=Action.DELETED,
        changes=changes,
        actor=user,
    )


def finalize_statement(statement, user, force=False):
    """Validate Σ transactions vs purchases_total and mark PROCESSED.

    Reversal lines are excluded: the bank books them under payments, so
    they never count toward the statement's purchases figure.
    """
    if statement.status == Status.PROCESSED:
        raise ValueError('El extracto ya está procesado.')
    total = statement.transactions.filter(
        is_reversal=False,
    ).aggregate(total=Sum('amount'))['total']
    total = total if total is not None else Decimal('0')
    difference = total - statement.purchases_total
    if abs(difference) > STATEMENT_TOTAL_TOLERANCE and not force:
        raise ValueError(
            f'La suma de las transacciones ({total}) no cuadra con el total '
            f'de compras del extracto ({statement.purchases_total}); '
            f'diferencia: {difference}. Corrige las transacciones o '
            'confirma el cierre forzado.'
        )
    return _set_status(statement, Status.PROCESSED, user)


def reopen_statement(statement, user):
    """Move a PROCESSED statement back to DRAFT for corrections."""
    if statement.status == Status.DRAFT:
        raise ValueError('El extracto ya está en borrador.')
    return _set_status(statement, Status.DRAFT, user)


def _set_status(statement, new_status, user):
    old_values = snapshot_values(statement, EntityType.STATEMENT)
    statement.status = new_status
    statement.save(update_fields=['status', 'updated_at'])
    change_log = log_accounting_change(
        entity_type=EntityType.STATEMENT,
        object_id=statement.pk,
        object_repr=object_repr(EntityType.STATEMENT, statement),
        action=Action.UPDATED,
        changes=compute_changes(
            EntityType.STATEMENT, old_values,
            snapshot_values(statement, EntityType.STATEMENT),
        ),
        actor=user,
    )
    accounting_service._notify(change_log)
    return statement


# ── Statement PDF ──

def _log_pdf_change(statement, old_name, new_name, user):
    """Silent audit row: the PDF is documentation, not accounting data."""
    _log_silent(
        EntityType.STATEMENT, statement, Action.UPDATED,
        [{
            'field': 'pdf_file',
            'label': 'PDF del extracto',
            'old': old_name,
            'new': new_name,
        }],
        user,
    )


def attach_statement_pdf(statement, file, user):
    """Attach (or replace) the bank PDF of a statement."""
    old_name = Path(statement.pdf_file.name).name if statement.pdf_file else ''
    if statement.pdf_file:
        statement.pdf_file.delete(save=False)
    statement.pdf_file = file
    statement.save(update_fields=['pdf_file', 'updated_at'])
    _log_pdf_change(statement, old_name, Path(file.name).name, user)
    return statement


def remove_statement_pdf(statement, user):
    """Delete the attached bank PDF from the statement and storage."""
    old_name = Path(statement.pdf_file.name).name
    statement.pdf_file.delete(save=False)
    statement.pdf_file = None
    statement.save(update_fields=['pdf_file', 'updated_at'])
    _log_pdf_change(statement, old_name, '', user)
    return statement


# ── Merchant aliases ──

def resolve_merchants(raw_descriptions):
    """Split descriptors into resolved, gateway-hint and unresolved lists.

    Gateway aliases are never returned as resolved: the last known
    merchant is only a starting point for manual verification.
    """
    resolved, gateway_hints, unresolved = [], [], []
    for raw in raw_descriptions:
        alias = MerchantAlias.objects.filter(
            match_text=normalize_descriptor(raw),
        ).first()
        if alias is None:
            unresolved.append(raw)
        elif alias.is_gateway:
            gateway_hints.append({
                'raw_description': raw,
                'last_known_merchant': alias.merchant_name,
                'category': alias.default_category,
                'alias_id': alias.pk,
                'note': (
                    'Pasarela de pago: el comercio real puede variar. '
                    'Verifica (recibo, correo) antes de asignar.'
                ),
            })
        else:
            resolved.append({
                'raw_description': raw,
                'merchant_name': alias.merchant_name,
                'category': alias.default_category,
                'alias_id': alias.pk,
            })
    return {
        'resolved': resolved,
        'gateway_hints': gateway_hints,
        'unresolved': unresolved,
    }


@transaction.atomic
def save_merchant_aliases(aliases_data, user, statement_id=None):
    """Upsert owner-approved aliases; optionally apply them to a draft.

    Each item: {'raw_description', 'merchant_name', 'category', 'is_gateway'}.
    Upserts by normalized match_text (re-approving is idempotent). Aliases
    are GLOBAL: they save regardless of any statement's state. With
    statement_id, matching transactions of that DRAFT statement get
    merchant/category and is_identified=True; if the statement is missing
    or already processed the aliases still save and a ``warning`` explains
    why nothing was applied. All audit rows are silent.
    """
    saved = []
    for data in aliases_data:
        match_text = normalize_descriptor(
            data.get('raw_description') or data.get('match_text') or '',
        )
        if not match_text:
            raise ValueError('Cada alias necesita una descripción a mapear.')
        alias, created = MerchantAlias.objects.update_or_create(
            match_text=match_text,
            defaults={
                'merchant_name': data['merchant_name'],
                'default_category': (
                    data.get('category') or TransactionCategory.OTHER
                ),
                'is_gateway': bool(data.get('is_gateway', False)),
                'created_by': (
                    user if getattr(user, 'is_authenticated', False) else None
                ),
            },
        )
        _log_silent(
            EntityType.MERCHANT_ALIAS, alias,
            Action.CREATED if created else Action.UPDATED,
            compute_changes(
                EntityType.MERCHANT_ALIAS, {},
                snapshot_values(alias, EntityType.MERCHANT_ALIAS),
            ),
            user,
        )
        saved.append(alias)

    updated_transactions = 0
    warning = ''
    if statement_id is not None:
        statement = CreditCardStatement.objects.filter(pk=statement_id).first()
        if statement is None:
            warning = (
                f'Los alias se guardaron, pero no se aplicaron: no existe '
                f'un extracto con id={statement_id}.'
            )
        elif statement.status != Status.DRAFT:
            warning = (
                'Los alias se guardaron, pero no se aplicaron: el extracto '
                'ya está procesado. Usa reopen_statement si necesitas '
                'aplicarlos a sus transacciones.'
            )
        else:
            updated_transactions = _apply_saved_aliases(saved, statement, user)
            if updated_transactions == 0:
                warning = (
                    'Los alias se guardaron, pero ninguno coincidió con '
                    'transacciones sin identificar del extracto.'
                )
    return {
        'aliases': saved,
        'updated_transactions': updated_transactions,
        'warning': warning,
    }


def _apply_saved_aliases(saved, statement, user):
    """Apply freshly saved non-gateway aliases to a draft's unidentified rows."""
    updated_transactions = 0
    by_match = {
        alias.match_text: alias for alias in saved if not alias.is_gateway
    }
    for tx in statement.transactions.filter(is_identified=False):
        alias = by_match.get(normalize_descriptor(tx.raw_description))
        if alias is None:
            continue
        old_values = snapshot_values(tx, EntityType.STATEMENT_TX)
        tx.merchant_name = alias.merchant_name
        tx.category = alias.default_category
        tx.is_identified = True
        tx.save(update_fields=[
            'merchant_name', 'category', 'is_identified', 'updated_at',
        ])
        _log_silent(
            EntityType.STATEMENT_TX, tx, Action.UPDATED,
            compute_changes(
                EntityType.STATEMENT_TX, old_values,
                snapshot_values(tx, EntityType.STATEMENT_TX),
            ),
            user,
        )
        updated_transactions += 1
    return updated_transactions


def delete_merchant_alias(alias, user):
    """Delete a learned alias (silent audit)."""
    deleted_id = alias.pk
    deleted_repr = object_repr(EntityType.MERCHANT_ALIAS, alias)
    old_values = snapshot_values(alias, EntityType.MERCHANT_ALIAS)
    alias.delete()
    log_accounting_change(
        entity_type=EntityType.MERCHANT_ALIAS,
        object_id=deleted_id,
        object_repr=deleted_repr,
        action=Action.DELETED,
        changes=[
            {'field': field, 'label': label,
             'old': old_values.get(field, ''), 'new': ''}
            for field, label in (
                ('match_text', 'Texto de coincidencia'),
                ('merchant_name', 'Comercio'),
                ('default_category', 'Categoría por defecto'),
            )
            if old_values.get(field, '') != ''
        ],
        actor=user,
    )


def update_merchant_alias(alias, serializer, user):
    """Apply a validated partial update to one alias (silent audit)."""
    old_values = snapshot_values(alias, EntityType.MERCHANT_ALIAS)
    alias = serializer.save()
    changes = compute_changes(
        EntityType.MERCHANT_ALIAS, old_values,
        snapshot_values(alias, EntityType.MERCHANT_ALIAS),
    )
    if changes:
        _log_silent(
            EntityType.MERCHANT_ALIAS, alias, Action.UPDATED, changes, user,
        )
    return alias


# ── Read helpers ──

def _statements_earliest_period(card_name=None):
    """First month with bank statements, from the active card catalog.

    None when no active catalog card declares ``statements_since`` — the
    grid then falls back to whatever statements actually exist.
    """
    catalog = CreditCard.objects.filter(
        is_active=True, statements_since__isnull=False,
    )
    if card_name:
        catalog = catalog.filter(name=card_name)
    return catalog.order_by('statements_since').values_list(
        'statements_since', flat=True,
    ).first()


def statement_month_status(year, card_name=None):
    """12-month grid: which months have processed/draft statements.

    ``year_options`` spans from the catalog's earliest statements_since
    (fallback: earliest existing statement) to the current year, and each
    month carries ``applies`` = False before statements existed.
    """
    queryset = CreditCardStatement.objects.filter(period_date__year=year)
    if card_name:
        queryset = queryset.filter(card_name=card_name)

    by_month = {}
    for statement in queryset:
        by_month.setdefault(statement.period_date.month, []).append(statement)

    earliest = _statements_earliest_period(card_name)

    months = []
    for month in range(1, 13):
        statements = by_month.get(month, [])
        months.append({
            'period': f'{year}-{month:02d}',
            'label': month_label(date(year, month, 1)),
            'applies': (
                earliest is None or date(year, month, 1) >= earliest
            ) or bool(statements),
            'statements': [
                {
                    'id': s.pk,
                    'card_name': s.card_name,
                    'status': s.status,
                    'status_label': s.get_status_display(),
                    'purchases_total': str(s.purchases_total),
                }
                for s in sorted(statements, key=lambda s: s.card_name)
            ],
            'has_processed': any(
                s.status == Status.PROCESSED for s in statements
            ),
            'has_draft': any(s.status == Status.DRAFT for s in statements),
        })

    current_year = today_bogota().year
    if earliest is not None:
        start_year = min(earliest.year, current_year)
    else:
        first_statement = (
            CreditCardStatement.objects.order_by('period_date')
            .values_list('period_date', flat=True)
            .first()
        )
        start_year = (
            min(first_statement.year, current_year)
            if first_statement else current_year
        )
    year_options = list(range(start_year, current_year + 1))

    cards = sorted(
        set(
            CreditCardStatement.objects.values_list('card_name', flat=True)
            .distinct()
        )
        | set(
            CreditCard.objects.filter(is_active=True)
            .values_list('name', flat=True)
        )
    )
    return {
        'year': year,
        'cards': cards,
        'months': months,
        'year_options': year_options,
    }


def statement_category_totals(statement):
    """Per-category sums for the detail payload / finalize summary."""
    labels = dict(TransactionCategory.choices)
    rows = (
        statement.transactions.values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    return [
        {
            'category': row['category'],
            'label': labels.get(row['category'], row['category']),
            'total': str(row['total'].quantize(Decimal('0.01'))),
        }
        for row in rows
    ]
