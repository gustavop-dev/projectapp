from django.db import models


class DiagnosticChangeLog(models.Model):
    """Audit trail for a WebAppDiagnostic."""

    class ChangeType(models.TextChoices):
        CREATED = 'created', 'Created'
        UPDATED = 'updated', 'Updated'
        SECTION_UPDATED = 'section_updated', 'Section Updated'
        SENT = 'sent', 'Sent'
        VIEWED = 'viewed', 'Viewed'
        NEGOTIATING = 'negotiating', 'Negotiating'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        FINISHED = 'finished', 'Finished'
        EMAIL_SENT = 'email_sent', 'Email Sent'
        NOTE = 'note', 'Note'
        CALL = 'call', 'Call'
        MEETING = 'meeting', 'Meeting'
        FOLLOWUP = 'followup', 'Follow-up'
        STATUS_CHANGE = 'status_change', 'Status Change'

    class ActorType(models.TextChoices):
        CLIENT = 'client', 'Client'
        SELLER = 'seller', 'Seller'
        SYSTEM = 'system', 'System'

    diagnostic = models.ForeignKey(
        'WebAppDiagnostic',
        on_delete=models.CASCADE,
        related_name='change_logs',
    )
    change_type = models.CharField(max_length=30, choices=ChangeType.choices)
    field_name = models.CharField(max_length=100, blank=True, default='')
    old_value = models.TextField(blank=True, default='')
    new_value = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    actor_type = models.CharField(
        max_length=10,
        choices=ActorType.choices,
        blank=True,
        default='',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Diagnostic Change Log'
        verbose_name_plural = 'Diagnostic Change Logs'

    def __str__(self):
        return f'{self.diagnostic.title} — {self.change_type} — {self.created_at}'
