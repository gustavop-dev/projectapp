from django.db import models

from .accounting_base import AccountingRecordBase


class NotificationRecipient(AccountingRecordBase):
    """Administrable destination list for the module's automated email.

    Every internal notification of the accounting module (change notices,
    card-debt and statement reminders, the payment calendar and the hosting
    payment outcomes) is delivered to the ``is_active`` rows of this table
    and to nobody else — no destination lives in code. ``created_at`` from
    the base is the "fecha de alta" shown in the panel, and ``is_active``
    pauses a recipient without losing the record (vacations, a change of
    responsible). Deactivating every row leaves the automation off in
    practice, which the panel warns about explicitly.

    The address is unique so the panel cannot register the same inbox
    twice; the serializer lowercases it first so the check is effectively
    case-insensitive.
    """

    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['email']
        verbose_name = 'Notification Recipient'
        verbose_name_plural = 'Notification Recipients'

    def __str__(self):
        return self.email
