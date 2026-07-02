from django.db import models

from .accounting_base import AccountingRecordBase, PartnerSplitMixin


class IncomeRecord(PartnerSplitMixin, AccountingRecordBase):
    """
    Income entry of the accounting module.

    A single model covers both expected income (projection) and liquid
    income (actually received): both share the same shape and the core
    dashboard question — expected vs liquid difference — becomes a
    single-table aggregate. A liquid record may point to the expected
    record it fulfills via `expected_income`.
    """

    class Kind(models.TextChoices):
        EXPECTED = 'expected', 'Esperado'
        LIQUID = 'liquid', 'Líquido'

    class Destination(models.TextChoices):
        PARTNERS = 'partners', 'Socios'
        POCKET = 'pocket', 'Bolsillo ProjectApp'

    concept = models.CharField(max_length=255)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    # Month granularity: always normalized to day 1 (serializer accepts "YYYY-MM").
    period_date = models.DateField()
    destination = models.CharField(
        max_length=10,
        choices=Destination.choices,
        default=Destination.PARTNERS,
    )
    expected_income = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='liquid_records',
        limit_choices_to={'kind': 'expected'},
    )
    # Auto-managed by accounting_service when kind=liquid and destination=pocket.
    pocket_movement = models.OneToOneField(
        'PocketMovement',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='income_record',
    )

    class Meta:
        ordering = ['-period_date', '-created_at']
        indexes = [
            models.Index(fields=['kind', 'period_date']),
        ]

    def __str__(self):
        return f'{self.concept} ({self.get_kind_display()} — {self.period_date:%Y-%m})'
