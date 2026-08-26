from django.db import models


class EmailLog(models.Model):
    """
    Tracks every email sent by the system for deliverability monitoring.
    """

    class Status(models.TextChoices):
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        BOUNCED = 'bounced', 'Bounced'
        FAILED = 'failed', 'Failed'
        SKIPPED = 'skipped', 'Omitida'

    class Audience(models.TextChoices):
        CLIENT = 'client', 'Al cliente'
        INTERNAL = 'internal', 'Interno'
        SECURITY = 'security', 'Seguridad'

    class DeliveryRole(models.TextChoices):
        PRIMARY = 'primary', 'Envío principal'
        COPY = 'copy', 'Copia interna'

    proposal = models.ForeignKey(
        'BusinessProposal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_logs',
    )
    template_key = models.CharField(max_length=100)
    recipient = models.EmailField()
    subject = models.CharField(max_length=500, blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SENT,
    )
    error_message = models.TextField(blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    # The rendered message, shared by every recipient of the same send.
    body = models.ForeignKey(
        'EmailBody',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
    )
    # What happened to the record that triggered the email, when the notice
    # is about a change ('' for the ones that are not).
    origin_action = models.CharField(
        max_length=10,
        blank=True,
        default='',
        choices=[
            ('created', 'Creado'),
            ('updated', 'Actualizado'),
            ('deleted', 'Eliminado'),
        ],
    )
    # Set when this row is a manual retry of an earlier failed send.
    retry_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retries',
    )
    # Who the email is about. Set on internal notices too: an accounting
    # change on this client's income never reached them, but it belongs in
    # their trail. SET_NULL rather than PROTECT because a client whose only
    # trace is an email row still passes every guard in
    # `delete_orphan_client`, which does not count emails either.
    client = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        # The composite index below already leads with this column; the
        # default FK index would be a redundant prefix of it.
        db_index=False,
        related_name='email_logs',
        limit_choices_to={'role': 'client'},
    )
    # Whether the message went to the client's own address or to the internal
    # recipient list. A fact of the send, not of the template: the composed
    # notices go to whatever address the panel typed into the composer, so no
    # template map can classify them. Defaults to INTERNAL because forgetting
    # it should under-count a client's contact, never inflate it.
    audience = models.CharField(
        max_length=10,
        choices=Audience.choices,
        default=Audience.INTERNAL,
    )
    # One UUID groups the primary row(s) and every independent internal-copy
    # attempt of the same physical customer delivery. Nullable preserves old
    # history without inventing associations during the migration.
    delivery_id = models.UUIDField(null=True, blank=True)
    delivery_role = models.CharField(
        max_length=10,
        choices=DeliveryRole.choices,
        default=DeliveryRole.PRIMARY,
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
        indexes = [
            models.Index(fields=['template_key', 'sent_at']),
            models.Index(fields=['status', 'sent_at']),
            models.Index(fields=['recipient']),
            models.Index(
                fields=['delivery_id', 'delivery_role'],
                name='emaillog_delivery_role',
            ),
            # Serves all three per-client annotations of the clients list:
            # the two counts seek on the (client, audience) prefix, and
            # `last_email_at` is a backwards scan of the sent_at suffix that
            # stops at the first row.
            models.Index(fields=['client', 'audience', 'sent_at'],
                         name='emaillog_client_aud_sent'),
        ]

    def __str__(self):
        return f'{self.template_key} → {self.recipient} ({self.status})'
