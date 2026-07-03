from django.db import models


class AccountingSettings(models.Model):
    """
    Singleton model storing accounting module configuration.

    Usage:
        settings = AccountingSettings.load()
        settings.notification_recipients  # → ['gustavo@...', 'carlos@...']
    """

    # List of email strings that receive change notifications.
    notification_recipients = models.JSONField(default=list, blank=True)
    notifications_enabled = models.BooleanField(default=True)

    # Weekly card-debt reminder (Fridays 9:00 Bogotá, re-alert every 2
    # days until a CardBalanceSnapshot dated >= that Friday exists).
    # cycle_start/last_sent_at are system state, not user settings.
    card_reminder_enabled = models.BooleanField(default=True)
    card_reminder_cycle_start = models.DateField(null=True, blank=True)
    card_reminder_last_sent_at = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Accounting settings'
        verbose_name_plural = 'Accounting settings'

    def __str__(self):
        recipients = ', '.join(self.notification_recipients) or '(sin destinatarios)'
        return f'AccountingSettings — {recipients}'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Return the singleton instance, creating it if needed."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
