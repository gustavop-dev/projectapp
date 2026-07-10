from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class HostingCycle(models.Model):
    """
    One paid billing cycle of a HostingRecord.

    History is the source of truth for money: the hosting's `total_paid`
    and `cycles_count` are denormalized sums recomputed by
    hosting_cycle_service on every cycle mutation. Each row snapshots the
    modality at payment time, so clients switching modality (semestral →
    trimestral) still add up correctly.

    `cycles_represented` > 1 only on the consolidated backfill row that
    carried the pre-history totals over (migration 0150).
    """

    hosting_record = models.ForeignKey(
        'content.HostingRecord',
        on_delete=models.CASCADE,
        related_name='cycles',
    )
    modality = models.CharField(max_length=12)
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    paid_at = models.DateField()
    period_from = models.DateField(null=True, blank=True)
    period_to = models.DateField(null=True, blank=True)
    cycles_represented = models.PositiveSmallIntegerField(default=1)
    notes = models.TextField(blank=True, default='')
    source_ref = models.CharField(
        max_length=64, blank=True, default='', db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-paid_at', '-id']

    def __str__(self):
        return f'{self.hosting_record_id} — {self.paid_at} — {self.amount}'
