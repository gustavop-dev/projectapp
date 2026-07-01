from django.db import models

from .accounting_base import AccountingRecordBase


class CardBalanceSnapshot(AccountingRecordBase):
    """Point-in-time credit card balance (available vs debt)."""

    snapshot_date = models.DateField()
    card_name = models.CharField(max_length=100)
    available_amount = models.DecimalField(max_digits=14, decimal_places=2)
    debt_amount = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ['-snapshot_date', '-created_at']
        indexes = [
            models.Index(fields=['card_name', 'snapshot_date']),
        ]

    def __str__(self):
        return f'{self.card_name} — {self.snapshot_date}'
