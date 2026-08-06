from django.db import models

from .accounting_base import AccountingRecordBase, PartnerSplitMixin


class IncomeRecord(PartnerSplitMixin, AccountingRecordBase):
    """
    Income entry of the accounting module.

    A single model covers expected income (projection), liquid income
    (actually received) and lost income (written off): they share the same
    shape and the core dashboard question — expected vs liquid difference —
    becomes a single-table aggregate. A liquid record may point to the
    expected record it fulfills via `expected_income`.

    Every aggregate filters `kind` explicitly, so `LOST` rows drop out of
    the projection and the utility without any of them having to know the
    kind exists.
    """

    class Kind(models.TextChoices):
        EXPECTED = 'expected', 'Esperado'
        LIQUID = 'liquid', 'Líquido'
        LOST = 'lost', 'Perdido'

    class Destination(models.TextChoices):
        PARTNERS = 'partners', 'Socios'
        POCKET = 'pocket', 'Bolsillo ProjectApp'

    class Origin(models.TextChoices):
        DEVELOPMENT = 'development', 'Desarrollo'
        HOSTING = 'hosting', 'Hosting'
        DIAGNOSTIC = 'diagnostic', 'Diagnóstico'
        OTHER = 'other', 'Otro'

    concept = models.CharField(max_length=255)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    # Optional on purpose: nearly every income has a client behind it, but a
    # refund or a financial yield may legitimately have none, and requiring
    # one would block the entry. PROTECT mirrors proposals and diagnostics —
    # a client with incomes cannot be deleted until they are resolved.
    client = models.ForeignKey(
        'accounts.UserProfile',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='income_records',
        limit_choices_to={'role': 'client'},
    )
    # Business line. Blank means "sin clasificar" (records predating the
    # field); hosting incomes rely on it because hosting clients are stored
    # as plain text and often have no platform profile to link to.
    origin = models.CharField(
        max_length=20, choices=Origin.choices, blank=True, default='',
    )
    # Month granularity by default (serializer accepts "YYYY-MM" → day 1);
    # a day other than 1 records the exact payment date when it is known.
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
            models.Index(fields=['client', 'period_date']),
        ]

    def __str__(self):
        return f'{self.concept} ({self.get_kind_display()} — {self.period_date:%Y-%m})'
