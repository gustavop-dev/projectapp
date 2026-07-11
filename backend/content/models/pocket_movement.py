from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from .accounting_base import AccountingRecordBase


class PocketMovement(AccountingRecordBase):
    """
    Ledger entry of the company pocket (Bolsillo ProjectApp).

    Direction + positive amount keeps validation trivial and aggregation
    explicit: balance = Sum(in) - Sum(out). Movements can be linked to an
    income or expense record (see the `pocket_movement` reverse relations);
    edits on either side of a linked pair are mirrored by accounting_service.
    """

    class Direction(models.TextChoices):
        IN = 'in', 'Ingreso'
        OUT = 'out', 'Egreso'

    concept = models.CharField(max_length=255)
    movement_date = models.DateField()
    direction = models.CharField(max_length=3, choices=Direction.choices)
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )

    class Meta:
        ordering = ['-movement_date', '-created_at']
        indexes = [
            models.Index(fields=['movement_date']),
        ]

    def __str__(self):
        sign = '+' if self.direction == self.Direction.IN else '-'
        return f'{self.concept} ({sign}{self.amount})'

    @property
    def linked_record(self):
        """The income or expense record this movement mirrors, if any."""
        return (
            getattr(self, 'income_record', None)
            or getattr(self, 'expense_record', None)
        )

    @property
    def is_auto_managed(self):
        """True when linked to an income or expense (name kept for API compat)."""
        return self.linked_record is not None
