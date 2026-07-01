from decimal import Decimal

from django.db import models

from .accounting_base import AccountingRecordBase


class HostingRecord(AccountingRecordBase):
    """
    Client hosting subscription registry (accounting view).

    Named HostingRecord to avoid confusion with accounts.HostingSubscription
    (Wompi-billed platform hosting). Hosting income itself is registered as
    IncomeRecord rows; this table tracks the per-client contract parameters.
    """

    class Modality(models.TextChoices):
        MONTHLY = 'monthly', 'Mensual'
        QUARTERLY = 'quarterly', 'Trimestral'
        SEMIANNUAL = 'semiannual', 'Semestral'
        ANNUAL = 'annual', 'Anual'

    MODALITY_MONTHS = {
        Modality.MONTHLY: 1,
        Modality.QUARTERLY: 3,
        Modality.SEMIANNUAL: 6,
        Modality.ANNUAL: 12,
    }

    client_name = models.CharField(max_length=255)
    domain_url = models.CharField(max_length=255, blank=True, default='')
    monthly_value = models.DecimalField(max_digits=14, decimal_places=2)
    payment_modality = models.CharField(
        max_length=12,
        choices=Modality.choices,
        default=Modality.MONTHLY,
    )
    benefit = models.CharField(max_length=255, blank=True, default='')
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    cycles_count = models.PositiveIntegerField(default=0)
    payment_per_cycle = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'),
    )
    total_paid = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'),
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['client_name']

    def __str__(self):
        return f'{self.client_name} — {self.domain_url or "(sin dominio)"}'
