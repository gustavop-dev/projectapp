from django.db import models


class ProposalRequirementItem(models.Model):
    """
    Individual functional requirement item within a group.

    Stores structured data for options and fields as JSON arrays,
    matching the schema expected by FunctionalRequirements.vue.
    """

    group = models.ForeignKey(
        'ProposalRequirementGroup',
        on_delete=models.CASCADE,
        related_name='items',
    )
    item_id = models.CharField(max_length=50)
    icon = models.CharField(max_length=10, default='✅')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    options = models.JSONField(default=list, blank=True)
    fields = models.JSONField(default=list, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Requirement Item'
        verbose_name_plural = 'Requirement Items'

    def __str__(self):
        return self.name
