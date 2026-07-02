from django.db import models

from .accounting_base import AccountingRecordBase, PartnerSplitMixin


class ExpenseRecord(PartnerSplitMixin, AccountingRecordBase):
    """
    Expense entry of the accounting module.

    Partner amounts represent each partner's share of the expense.
    Expenses paid from the company pocket get an auto-managed OUT
    pocket movement (see accounting_service).
    """

    class Category(models.TextChoices):
        BUSINESS = 'business', 'Negocio'
        PERSONAL = 'personal', 'Personal'

    class PaidFrom(models.TextChoices):
        PARTNERS = 'partners', 'Socios'
        POCKET = 'pocket', 'Bolsillo ProjectApp'

    concept = models.CharField(max_length=255)
    # Month granularity: always normalized to day 1 (serializer accepts "YYYY-MM").
    period_date = models.DateField()
    category = models.CharField(
        max_length=10,
        choices=Category.choices,
        default=Category.BUSINESS,
    )
    paid_from = models.CharField(
        max_length=10,
        choices=PaidFrom.choices,
        default=PaidFrom.PARTNERS,
    )
    # Auto-managed by accounting_service when paid_from=pocket.
    pocket_movement = models.OneToOneField(
        'PocketMovement',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='expense_record',
    )

    class Meta:
        ordering = ['-period_date', '-created_at']
        indexes = [
            models.Index(fields=['period_date']),
        ]

    def __str__(self):
        return f'{self.concept} ({self.period_date:%Y-%m})'
