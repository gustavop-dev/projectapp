from django.db import models

from .accounting_base import AccountingRecordBase


class CreditCard(AccountingRecordBase):
    """Catalog of credit cards managed from the accounting settings.

    ``name`` is the human identifier reused as the plain-string
    ``card_name`` on snapshots/statements (no FK on purpose: historical
    rows keep whatever name they were written with). ``credit_limit`` is
    the current cupo — snapshots store the debt computed at write time,
    so editing the cupo never rewrites history. ``statements_since``
    marks the first month (day 1) with bank statements for the card.
    """

    name = models.CharField(max_length=100, unique=True)
    credit_limit = models.DecimalField(max_digits=14, decimal_places=2)
    is_active = models.BooleanField(default=True)
    statements_since = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Credit Card'
        verbose_name_plural = 'Credit Cards'

    def __str__(self):
        return self.name
