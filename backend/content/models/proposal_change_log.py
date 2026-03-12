from django.db import models


class ProposalChangeLog(models.Model):
    """
    Tracks changes to a business proposal over time.

    Each row represents a single event or field change, enabling
    a full audit trail and version history for the proposal lifecycle.
    """

    class ChangeType(models.TextChoices):
        CREATED = 'created', 'Created'
        UPDATED = 'updated', 'Updated'
        SENT = 'sent', 'Sent'
        VIEWED = 'viewed', 'Viewed'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        RESENT = 'resent', 'Resent'
        EXPIRED = 'expired', 'Expired'
        DUPLICATED = 'duplicated', 'Duplicated'
        COMMENTED = 'commented', 'Commented'
        NEGOTIATING = 'negotiating', 'Negotiating'
        REENGAGEMENT = 'reengagement', 'Reengagement'
        CALL = 'call', 'Call'
        MEETING = 'meeting', 'Meeting'
        FOLLOWUP = 'followup', 'Follow-up'
        NOTE = 'note', 'Note'
        CALCULATOR_CONFIRMED = 'calc_confirmed', 'Calculator Confirmed'
        CALCULATOR_ABANDONED = 'calc_abandoned', 'Calculator Abandoned'
        AUTO_ARCHIVED = 'auto_archived', 'Auto Archived'
        STATUS_CHANGE = 'status_change', 'Status Change'
        CONDITIONAL_ACCEPT = 'cond_accepted', 'Conditional Acceptance'
        CALCULATOR_FOLLOWUP = 'calc_followup', 'Calculator Follow-up Sent'

    proposal = models.ForeignKey(
        'BusinessProposal',
        on_delete=models.CASCADE,
        related_name='change_logs',
    )
    change_type = models.CharField(
        max_length=20,
        choices=ChangeType.choices,
    )
    field_name = models.CharField(max_length=100, blank=True, default='')
    old_value = models.TextField(blank=True, default='')
    new_value = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Proposal Change Log'
        verbose_name_plural = 'Proposal Change Logs'

    def __str__(self):
        return (
            f'{self.proposal.client_name} — '
            f'{self.change_type} — {self.created_at}'
        )
