from django.db import models


class ProposalViewEvent(models.Model):
    """
    Records each client visit/page-load of a business proposal.

    A single proposal may have many view events (one per page-load).
    The session_id groups section views within a single browsing session.
    """

    proposal = models.ForeignKey(
        'BusinessProposal',
        on_delete=models.CASCADE,
        related_name='view_events',
    )
    session_id = models.CharField(
        max_length=64,
        help_text='Client-side generated session identifier.',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']
        verbose_name = 'Proposal View Event'
        verbose_name_plural = 'Proposal View Events'

    def __str__(self):
        return (
            f'{self.proposal.client_name} — '
            f'Session {self.session_id[:8]} — {self.viewed_at}'
        )
