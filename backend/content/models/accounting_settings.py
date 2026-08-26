from decimal import Decimal

from django.db import models, transaction


class AccountingSettings(models.Model):
    """
    Singleton model storing accounting module configuration.

    Usage:
        settings = AccountingSettings.load()
        settings.notifications_enabled  # → master switch
    """

    # Master switch for every automated email of the module. Who receives
    # them lives in the NotificationRecipient table (one administrable row
    # per address); read it through
    # ``services.notification_recipient_service.active_recipient_emails``.
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

    # Global landing preferences for /panel/accounting/collections. Unlike
    # incomes, the in-page controls persist their last confirmed value so the
    # next visit (and every superuser/device) opens the same way.
    class CollectionAccountsViewMode(models.TextChoices):
        GROUPED = 'grouped', 'Agrupado'
        CLASSIC = 'classic', 'Clásico'

    class CollectionAccountsGroupBy(models.TextChoices):
        CLIENT = 'client', 'Cliente'
        PROJECT = 'project', 'Proyecto'

    collection_accounts_view_mode = models.CharField(
        max_length=10,
        choices=CollectionAccountsViewMode.choices,
        default=CollectionAccountsViewMode.GROUPED,
    )
    collection_accounts_group_by = models.CharField(
        max_length=10,
        choices=CollectionAccountsGroupBy.choices,
        default=CollectionAccountsGroupBy.CLIENT,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Accounting settings'
        verbose_name_plural = 'Accounting settings'

    def __str__(self):
        state = 'activas' if self.notifications_enabled else 'pausadas'
        return f'AccountingSettings — notificaciones {state}'

    def save(self, *args, **kwargs):
        self.pk = 1
        with transaction.atomic():
            previous_rate = type(self).objects.filter(pk=1).values_list(
                'usd_exchange_rate', flat=True,
            ).first()
            super().save(*args, **kwargs)
            persisted_rate = type(self).objects.values_list(
                'usd_exchange_rate', flat=True,
            ).get(pk=1)
            if previous_rate != persisted_rate:
                # Local import avoids a model-module cycle at Django startup.
                from .recurring_payment import RecurringPayment

                RecurringPayment.synchronize_cop_equivalents(persisted_rate)

    @classmethod
    def load(cls):
        """Return the singleton instance, creating it if needed."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
