import uuid

from django.db import models


class ProposalShareLink(models.Model):
    """
    Tracked sharing link for multi-stakeholder proposal viewing.

    When a client shares the proposal with their team, a new share link
    is created with a unique UUID. Each viewer's access is tracked
    independently from the main proposal view count.
    """

    proposal = models.ForeignKey(
        'BusinessProposal',
        on_delete=models.CASCADE,
        related_name='share_links',
    )
    uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, db_index=True
    )
    shared_by_name = models.CharField(max_length=255)
    shared_by_email = models.EmailField(blank=True, default='')
    recipient_name = models.CharField(max_length=255, blank=True, default='')
    recipient_email = models.EmailField(blank=True, default='')
    view_count = models.PositiveIntegerField(default=0)
    first_viewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Proposal Share Link'
        verbose_name_plural = 'Proposal Share Links'

    def __str__(self):
        return (
            f'{self.proposal.client_name} → '
            f'{self.recipient_name or "pending"} — {self.uuid}'
        )
