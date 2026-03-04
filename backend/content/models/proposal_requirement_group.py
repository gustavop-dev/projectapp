from django.db import models


class ProposalRequirementGroup(models.Model):
    """
    A group of functional requirements within a proposal.

    Examples: Views, Components, Features. Each group contains
    multiple ProposalRequirementItem instances.
    """

    proposal = models.ForeignKey(
        'BusinessProposal',
        on_delete=models.CASCADE,
        related_name='requirement_groups',
    )
    group_id = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Requirement Group'
        verbose_name_plural = 'Requirement Groups'

    def __str__(self):
        return f'{self.proposal.client_name} — {self.title}'
