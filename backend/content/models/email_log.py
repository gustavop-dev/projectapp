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
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
        indexes = [
            models.Index(fields=['template_key', 'sent_at']),
            models.Index(fields=['status', 'sent_at']),
        ]

    def __str__(self):
        return f'{self.template_key} → {self.recipient} ({self.status})'
