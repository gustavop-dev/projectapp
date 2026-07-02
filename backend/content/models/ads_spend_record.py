from django.db import models

from .accounting_base import AccountingRecordBase


class AdsSpendRecord(AccountingRecordBase):
    """
    Single advertising spend entry (Facebook/Google Ads).

    The running "accumulated" figure is always computed at read time
    (see accounting_service.ads_with_accumulated) — never stored, so it
    stays correct after edits and deletes.
    """

    class Platform(models.TextChoices):
        FACEBOOK = 'facebook', 'Facebook Ads'
        GOOGLE = 'google', 'Google Ads'
        OTHER = 'other', 'Otro'

    spend_date = models.DateField()
    platform = models.CharField(
        max_length=10, choices=Platform.choices, default=Platform.FACEBOOK,
    )
    origin_card = models.CharField(max_length=100, blank=True, default='')
    amount = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ['-spend_date', '-created_at']
        indexes = [
            models.Index(fields=['platform', 'spend_date']),
        ]

    def __str__(self):
        return f'{self.get_platform_display()} — {self.spend_date} — {self.amount}'
