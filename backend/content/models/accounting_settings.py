from decimal import Decimal

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

    # Statement reminder (every 8 days while the previous month's statement
    # of an active catalog card is missing, draft or lacks its PDF).
    # last_sent_at is system state, not a user setting.
    statement_reminder_enabled = models.BooleanField(default=True)
    statement_reminder_last_sent_at = models.DateField(null=True, blank=True)

    # Hosting expiry notices (15/7 days before valid_to, then every 5 days
    # until the cuenta de cobro is sent). Delivered as a section of the daily
    # payment calendar below, so this toggle now governs that section.
    hosting_expiry_reminder_enabled = models.BooleanField(default=True)

    # Daily payment calendar: one consolidated email with the expected incomes,
    # the next charge of the recurring payments and the hostings about to
    # expire — 15 days ahead, 7 days ahead and on the date itself.
    payment_calendar_enabled = models.BooleanField(default=True)

    # How often an expected income that passed its date keeps being reminded
    # until it is collected or muted. The first cadence in the module the
    # operator can edit; every other one is a module constant.
    class OverdueFrequency(models.TextChoices):
        WEEKLY = 'weekly', 'Semanal'
        BIWEEKLY = 'biweekly', 'Quincenal'

    overdue_reminder_frequency = models.CharField(
        max_length=10,
        choices=OverdueFrequency.choices,
        default=OverdueFrequency.BIWEEKLY,
    )

    # Reference COP-per-USD rate for USD KPIs (editable from the panel).
    usd_exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('4000'),
    )

    # How /panel/accounting/incomes lands on every visit; the in-page
    # toggle only lasts the session (deliberately not persisted).
    class IncomeViewMode(models.TextChoices):
        GROUPED = 'grouped', 'Agrupado'
        CLASSIC = 'classic', 'Clásico'

    income_default_view_mode = models.CharField(
        max_length=10,
        choices=IncomeViewMode.choices,
        default=IncomeViewMode.GROUPED,
    )

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
