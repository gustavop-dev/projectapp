from django.db import models


class ProposalProjectStage(models.Model):
    """
    Internal project execution tracking — start/end dates per stage,
    used by the daily Huey task `notify_proposal_stage_deadlines` to email
    the team about deadlines (70% pre-warning + overdue reminders).

    Distinct from the `development_stages` proposal section, which is
    client-facing display content. This model is internal-only and never
    rendered to the client.
    """

    class StageKey(models.TextChoices):
        DESIGN = 'design', 'Diseño'
        DEVELOPMENT = 'development', 'Desarrollo'

    proposal = models.ForeignKey(
        'BusinessProposal',
        on_delete=models.CASCADE,
        related_name='project_stages',
    )
    stage_key = models.CharField(
        max_length=30,
        choices=StageKey.choices,
    )
    order = models.PositiveSmallIntegerField(default=0)

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(
        null=True, blank=True,
        help_text='When an admin marked this stage as completed. Silences alerts.',
    )

    warning_sent_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Timestamp of the 70% pre-deadline warning email. Sent once.',
    )
    last_overdue_reminder_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Timestamp of the most recent overdue reminder email '
                  '(first one + every 3 days while uncompleted).',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('proposal', 'stage_key')]
        ordering = ['proposal_id', 'order']
        verbose_name = 'Proposal Project Stage'
        verbose_name_plural = 'Proposal Project Stages'

    def __str__(self):
        return f'{self.proposal_id} — {self.get_stage_key_display()}'
