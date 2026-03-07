from django.db import models


class ProposalSectionView(models.Model):
    """
    Records time spent on a specific section within a proposal view session.

    Each row represents one section the client navigated to during a single
    browsing session, along with how long they spent on it.
    """

    view_event = models.ForeignKey(
        'ProposalViewEvent',
        on_delete=models.CASCADE,
        related_name='section_views',
    )
    section_type = models.CharField(max_length=50)
    section_title = models.CharField(max_length=255, blank=True, default='')
    time_spent_seconds = models.FloatField(
        default=0,
        help_text='Seconds the client spent viewing this section.',
    )
    entered_at = models.DateTimeField(
        help_text='Timestamp when the client navigated to this section.',
    )

    class Meta:
        ordering = ['entered_at']
        verbose_name = 'Proposal Section View'
        verbose_name_plural = 'Proposal Section Views'

    def __str__(self):
        return (
            f'{self.view_event.proposal.client_name} — '
            f'{self.section_type} — {self.time_spent_seconds:.1f}s'
        )
