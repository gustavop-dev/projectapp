from django.db import models

from .accounting_change_log import AccountingChangeLog


# The accounting vocabulary plus the one record that can originate an email
# without being an audit entity itself. Sharing the base list keeps the
# target types from drifting away from the audit trail's — which now names
# 'collection_account' (and 'project') directly.
ENTITY_TYPE_CHOICES = AccountingChangeLog.EntityType.choices + [
    ('payment', 'Pago de plataforma'),
]


class EmailLogTarget(models.Model):
    """
    Which records an email talked about.

    One row per record named by an ``EmailLog``. The digest notices (payment
    calendar, card debt, statements) cover several records at once, so a pair
    of columns on ``EmailLog`` could not answer "what went out for this
    hosting". Records are identified by ``entity_type`` + ``object_id`` with
    no real FK, for the same reason ``AccountingChangeLog`` does it: the trail
    has to survive the record's deletion, and ``object_repr`` keeps the
    human-readable identity once the record is gone.
    """

    email_log = models.ForeignKey(
        'EmailLog',
        on_delete=models.CASCADE,
        related_name='targets',
    )
    entity_type = models.CharField(max_length=30, choices=ENTITY_TYPE_CHOICES)
    object_id = models.PositiveIntegerField()
    object_repr = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        verbose_name = 'Email Log Target'
        verbose_name_plural = 'Email Log Targets'
        constraints = [
            models.UniqueConstraint(
                fields=['email_log', 'entity_type', 'object_id'],
                name='uniq_email_log_target',
            ),
        ]
        indexes = [
            models.Index(fields=['entity_type', 'object_id']),
        ]

    def __str__(self):
        return f'{self.entity_type}#{self.object_id} → log {self.email_log_id}'
