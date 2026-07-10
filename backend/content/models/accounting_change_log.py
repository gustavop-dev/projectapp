from django.conf import settings
from django.db import models


class AccountingChangeLog(models.Model):
    """
    Audit trail for the accounting module.

    One row per action (create/update/delete) with the full field diff in
    `changes`. Records are identified by entity_type + object_id (no real
    FK: audit rows must survive record deletion) and `object_repr` keeps
    the human-readable identity after the record is gone.
    """

    class EntityType(models.TextChoices):
        INCOME = 'income', 'Ingreso'
        EXPENSE = 'expense', 'Gasto'
        HOSTING = 'hosting', 'Hosting'
        POCKET = 'pocket', 'Bolsillo'
        RECURRING = 'recurring', 'Pago recurrente'
        ADS = 'ads', 'Ads'
        CARD_SNAPSHOT = 'card_snapshot', 'Saldo tarjeta'
        STATEMENT = 'statement', 'Extracto de tarjeta'
        STATEMENT_TX = 'statement_tx', 'Transacción de extracto'
        MERCHANT_ALIAS = 'merchant_alias', 'Alias de comercio'
        SETTINGS = 'settings', 'Configuración'

    class Action(models.TextChoices):
        CREATED = 'created', 'Creado'
        UPDATED = 'updated', 'Actualizado'
        DELETED = 'deleted', 'Eliminado'

    entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    object_id = models.PositiveIntegerField()
    object_repr = models.CharField(max_length=255)
    action = models.CharField(max_length=10, choices=Action.choices)
    # List of {'field': str, 'label': str, 'old': str, 'new': str}.
    changes = models.JSONField(default=list, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    actor_username = models.CharField(max_length=150, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['entity_type', 'object_id', 'created_at']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Accounting Change Log'
        verbose_name_plural = 'Accounting Change Logs'

    def __str__(self):
        return (
            f'{self.get_entity_type_display()} — '
            f'{self.get_action_display()} — {self.object_repr}'
        )
