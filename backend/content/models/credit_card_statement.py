"""Credit-card statement ledger (extractos de tarjeta de crédito).

Analytical sub-module of the accounting app: one statement per card+month
with its billed line items, fed by the MCP assistant from the bank PDF.
It NEVER creates ExpenseRecords or PocketMovements — per the operating
model, expenses leave the pocket and only the card payment (abono) is
registered in the main ledgers.
"""

from django.db import models

from .accounting_base import AccountingRecordBase


def normalize_descriptor(raw):
    """Canonical form of a statement descriptor for alias matching.

    Uppercase, collapse whitespace and drop digit-only tokens of 5+ digits
    (auth codes, reference numbers) so 'PAYU*NETFLIX 990011' normalizes to
    'PAYU*NETFLIX'. Shorter numbers stay: they are usually part of the
    merchant's name ('HOSTEL 265', 'STUDIO 54') or a stable store number.
    Deterministic on purpose: exact matches only, no fuzzy lookups.
    """
    return ' '.join(
        token for token in str(raw or '').upper().split()
        if not (token.isdigit() and len(token) >= 5)
    )


class TransactionCategory(models.TextChoices):
    SOFTWARE = 'software', 'Software y suscripciones'
    ADVERTISING = 'advertising', 'Publicidad'
    FUEL = 'fuel', 'Gasolina'
    GROCERIES = 'groceries', 'Supermercado'
    RESTAURANTS = 'restaurants', 'Restaurantes'
    UTILITIES = 'utilities', 'Servicios'
    TRAVEL = 'travel', 'Viajes'
    SHOPPING = 'shopping', 'Compras'
    OTHER = 'other', 'Otros'


class CreditCardStatement(AccountingRecordBase):
    """One monthly statement of one credit card.

    ``purchases_total`` is the statement's own purchases figure and anchors
    the finalize validation (Σ transactions must match it). Interest, fees
    and payments are header-level totals, never transactions. Optional
    totals are nullable because "the bank didn't report it" ≠ 0.
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Borrador'
        PROCESSED = 'processed', 'Procesado'

    card_name = models.CharField(max_length=100, db_index=True)
    period_date = models.DateField()  # always day 1 (MonthPeriodField)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT,
    )
    purchases_total = models.DecimalField(max_digits=14, decimal_places=2)
    previous_balance = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
    )
    payments_total = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
    )
    interest_and_fees = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
    )
    closing_balance = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
    )
    minimum_payment = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
    )
    due_date = models.DateField(null=True, blank=True)
    # Bank PDF kept as documentation once the statement is processed.
    pdf_file = models.FileField(
        upload_to='statement_pdfs/%Y/%m/', null=True, blank=True,
    )

    class Meta:
        ordering = ['-period_date', 'card_name']
        constraints = [
            models.UniqueConstraint(
                fields=['card_name', 'period_date'],
                name='uniq_statement_card_period',
            ),
        ]
        verbose_name = 'Credit Card Statement'
        verbose_name_plural = 'Credit Card Statements'

    def __str__(self):
        return f'{self.card_name} — {self.period_date:%Y-%m}'


class CreditCardTransaction(AccountingRecordBase):
    """One billed line of a statement.

    ``amount`` is the COP value the line contributes to the statement's
    "Compras del mes" figure (a new installment purchase carries the FULL
    purchase value; the installment plan lives in ``installment_number`` /
    ``installments_total``). Reversals are negative lines flagged with
    ``is_reversal``: they neutralize the category breakdown but are excluded
    from the finalize sum, because the bank books them under payments, not
    purchases. ``raw_description`` keeps the statement text exactly as
    printed — it feeds alias learning.
    """

    statement = models.ForeignKey(
        CreditCardStatement,
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    transaction_date = models.DateField()
    raw_description = models.CharField(max_length=255)
    merchant_name = models.CharField(max_length=150, blank=True, default='')
    category = models.CharField(
        max_length=20,
        choices=TransactionCategory.choices,
        default=TransactionCategory.OTHER,
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    original_amount = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
    )
    original_currency = models.CharField(max_length=3, blank=True, default='')
    installment_number = models.PositiveSmallIntegerField(null=True, blank=True)
    installments_total = models.PositiveSmallIntegerField(null=True, blank=True)
    is_identified = models.BooleanField(default=False)
    is_reversal = models.BooleanField(default=False)

    class Meta:
        ordering = ['transaction_date', 'id']
        indexes = [
            models.Index(fields=['statement', 'transaction_date']),
        ]
        verbose_name = 'Credit Card Transaction'
        verbose_name_plural = 'Credit Card Transactions'

    def __str__(self):
        return f'{self.merchant_name or self.raw_description} — {self.amount}'


class MerchantAlias(AccountingRecordBase):
    """Learned mapping raw statement descriptor → merchant + category.

    ``match_text`` is ALWAYS stored normalized (see normalize_descriptor);
    resolution is an exact lookup on it. Approved in chat by the owner
    before being saved — never auto-learned. ``is_gateway`` marks payment
    processors (EBANX, MERCADOPAGO, DLOCAL...) whose descriptor hides the
    real merchant: the alias keeps the knowledge but is never auto-applied,
    it only surfaces as a hint for manual review.
    """

    match_text = models.CharField(max_length=255, unique=True)
    merchant_name = models.CharField(max_length=150)
    default_category = models.CharField(
        max_length=20,
        choices=TransactionCategory.choices,
        default=TransactionCategory.OTHER,
    )
    is_gateway = models.BooleanField(default=False)

    class Meta:
        ordering = ['match_text']
        verbose_name = 'Merchant Alias'
        verbose_name_plural = 'Merchant Aliases'

    def __str__(self):
        return f'{self.match_text} → {self.merchant_name}'
