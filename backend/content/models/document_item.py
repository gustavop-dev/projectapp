from django.db import models


class DocumentItem(models.Model):
    """Line items for a commercial document."""

    class ItemType(models.TextChoices):
        SERVICE = 'service', 'Service'
        HOSTING = 'hosting', 'Hosting'
        SUPPORT = 'support', 'Support'
        ADVANCE = 'advance', 'Advance'
        BALANCE = 'balance', 'Balance'
        ADJUSTMENT = 'adjustment', 'Adjustment'
        OTHER = 'other', 'Other'

    document = models.ForeignKey(
        'content.Document',
        on_delete=models.CASCADE,
        related_name='items',
    )
    position = models.PositiveIntegerField(default=0)
    item_type = models.CharField(
        max_length=32,
        choices=ItemType.choices,
        default=ItemType.SERVICE,
    )
    description = models.CharField(max_length=1024)
    quantity = models.DecimalField(max_digits=14, decimal_places=4, default=1)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    reference_type = models.CharField(max_length=64, blank=True, default='')
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['document_id', 'position', 'id']

    def __str__(self):
        return f'Item {self.position} doc={self.document_id}'
