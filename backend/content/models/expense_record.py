from django.db import models

from .accounting_base import AccountingRecordBase, PartnerSplitMixin


class ExpenseRecordQuerySet(models.QuerySet):
    """Splits real spending from money that never arrived."""

    def operational(self):
        """Expenses that reduce utility (everything but income deductions)."""
        return self.filter(deduction_type='')

    def deductions(self):
        """Gateway/bank fees and withholdings discounted from an income."""
        return self.exclude(deduction_type='')


class ExpenseRecord(PartnerSplitMixin, AccountingRecordBase):
    """
    Expense entry of the accounting module.

    Partner amounts represent each partner's share of the expense.
    Every expense draws from money already in the pocket, so new expenses
    keep a linked pocket OUT movement in sync (see accounting_service);
    records created before the linkage existed stay unlinked.

    ``deduction_type`` marks the rows that are NOT operational spending but a
    discount taken out of an income before it landed (a Wompi fee, a bank fee,
    a withholding). Those are excluded from utility on purpose: the settlement
    lowers the expected income to what was actually received, so the money is
    already missing from the liquid total and subtracting it again would count
    the same loss twice.
    """

    class Category(models.TextChoices):
        BUSINESS = 'business', 'Negocio'
        PERSONAL = 'personal', 'Personal'

    class DeductionType(models.TextChoices):
        GATEWAY_FEE = 'gateway_fee', 'Comisión plataforma de pago'
        BANK_FEE = 'bank_fee', 'Comisión bancaria'
        WITHHOLDING = 'withholding', 'Retención en la fuente'
        OTHER = 'other', 'Otro'

    concept = models.CharField(max_length=255)
    # Month granularity by default (serializer accepts "YYYY-MM" → day 1);
    # a day other than 1 records the exact payment date when it is known.
    period_date = models.DateField()
    category = models.CharField(
        max_length=10,
        choices=Category.choices,
        default=Category.BUSINESS,
    )
    # Blank for ordinary expenses; set only by the income settlement flow.
    # Its presence IS the "this is an income deduction" flag — no extra boolean.
    deduction_type = models.CharField(
        max_length=20,
        choices=DeductionType.choices,
        blank=True,
        default='',
    )
    # Auto-managed pocket OUT movement kept in sync by accounting_service.
    pocket_movement = models.OneToOneField(
        'PocketMovement',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='expense_record',
    )

    objects = ExpenseRecordQuerySet.as_manager()

    class Meta:
        ordering = ['-period_date', '-created_at']
        indexes = [
            models.Index(fields=['period_date']),
        ]

    def __str__(self):
        return f'{self.concept} ({self.period_date:%Y-%m})'
