from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AccountingRecordBase(models.Model):
    """
    Common plumbing shared by every accounting entity.

    `source_ref` is an idempotency key: `import:<hash>` for spreadsheet
    imports, `fake:<tag>` for fake data, empty for manual records.
    """

    notes = models.TextField(blank=True, default='')
    source_ref = models.CharField(
        max_length=64,
        blank=True,
        default='',
        db_index=True,
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
        abstract = True


class PartnerSplitMixin(models.Model):
    """
    Total amount plus editable per-partner amounts.

    Amounts (not percentages) are the source of truth, mirroring the
    original spreadsheet. The 50/50 default is applied at serializer
    level so explicit zeros are respected. Whatever is not assigned to
    a partner belongs to the company pocket (`company_amount`).
    """

    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    gustavo_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'),
    )
    carlos_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0'),
    )

    class Meta:
        abstract = True

    @property
    def company_amount(self):
        return self.total_amount - self.gustavo_amount - self.carlos_amount

    def clean(self):
        super().clean()
        for field in ('total_amount', 'gustavo_amount', 'carlos_amount'):
            value = getattr(self, field)
            if value is not None and value < 0:
                raise ValidationError(
                    {field: 'Los montos no pueden ser negativos.'}
                )
        if (
            self.total_amount is not None
            and self.gustavo_amount is not None
            and self.carlos_amount is not None
            and self.gustavo_amount + self.carlos_amount > self.total_amount
        ):
            raise ValidationError(
                'La suma de los montos de los socios no puede superar el monto total.'
            )
