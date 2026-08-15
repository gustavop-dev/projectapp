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
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
        indexes = [
            models.Index(fields=['template_key', 'sent_at']),
            models.Index(fields=['status', 'sent_at']),
            models.Index(fields=['recipient']),
        ]

    def __str__(self):
        return f'{self.template_key} → {self.recipient} ({self.status})'
