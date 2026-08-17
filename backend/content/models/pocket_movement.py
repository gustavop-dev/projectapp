from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from .accounting_base import AccountingRecordBase, Ledger


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
    def income_children(self):
        """Liquid incomes covered by this movement (an abono may hold several).

        Memoized on the instance because the serializer reads it more than
        once per row; `self.income_records.all()` reuses a prefetch cache
        when the queryset provided one.
        """
        cache = getattr(self, '_income_children_cache', None)
        if cache is None:
            # Sorted in Python (pk == creation == allocation order): an
            # order_by() here would bypass the prefetch cache and pay one
            # query per row on the pocket list.
            cache = sorted(
                self.income_records.all(), key=lambda record: record.pk,
            )
            self._income_children_cache = cache
        return cache

    @property
    def is_shared(self):
        """True when this movement is an abono covering more than one income."""
        return len(self.income_children) > 1

    @property
    def linked_record(self):
        """The single record this movement mirrors, if any.

        Deliberately None for a shared (abono) movement: it mirrors no single
        record, so every mirror/edit path that keys on this property treats it
        like a historical unlinked movement and touches no child.
        """
        children = self.income_children
        if len(children) == 1:
            return children[0]
        if children:
            return None
        return getattr(self, 'expense_record', None)

    @property
    def is_auto_managed(self):
        """True when linked to incomes or an expense (name kept for API compat)."""
        return bool(self.income_children) or (
            getattr(self, 'expense_record', None) is not None
        )

    @property
    def attribution(self):
        """Party this movement is effectively attributed to, or None.

        OUT mirrors are company expenses whose split says whose draw it was,
        so the answer there is the expense's `partner_attribution`. IN mirrors
        derive from their income children's ledger: the children of a valid
        movement are unanimous (pocket incomes are company by the write rules,
        and an abono's N children doubly so), so the unanimous ledger is the
        answer; a mixed set is only reachable through invalid direct writes
        and falls to COMPANY, mirroring what the SQL's company branch matches.
        Unlinked historical movements mirror nothing and have no attribution.

        `_POCKET_ATTRIBUTION_Q` in `content.views.accounting` restates this rule
        in SQL so the table, the CSV export and the MCP tool cut the same rows.
        Keep both sides in sync.
        """
        expense = getattr(self, 'expense_record', None)
        if expense is not None:
            return expense.partner_attribution
        ledgers = {child.ledger for child in self.income_children}
        if len(ledgers) == 1:
            return next(iter(ledgers))
        if ledgers:
            return Ledger.COMPANY
        return None
