from django.db import models


class DiagnosticViewEvent(models.Model):
    """Records each client visit/page-load of a WebAppDiagnostic."""

    diagnostic = models.ForeignKey(
        'WebAppDiagnostic',
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
        verbose_name = 'Diagnostic View Event'
        verbose_name_plural = 'Diagnostic View Events'
        constraints = [
            models.UniqueConstraint(
                fields=['diagnostic', 'session_id'],
                name='uniq_diagnosticviewevent_diagnostic_session',
            ),
        ]
        indexes = [
            models.Index(fields=['diagnostic', 'viewed_at']),
        ]

    def __str__(self):
        return (
            f'{self.diagnostic.title} — '
            f'Session {self.session_id[:8]} — {self.viewed_at}'
        )


class DiagnosticSectionView(models.Model):
    """Time spent on a section within a diagnostic view session."""

    view_event = models.ForeignKey(
        'DiagnosticViewEvent',
        on_delete=models.CASCADE,
        related_name='section_views',
    )
    section_type = models.CharField(max_length=50)
    section_title = models.CharField(max_length=255, blank=True, default='')
    time_spent_seconds = models.FloatField(default=0)
    entered_at = models.DateTimeField()

    class Meta:
        ordering = ['entered_at']
        verbose_name = 'Diagnostic Section View'
        verbose_name_plural = 'Diagnostic Section Views'
        indexes = [
            models.Index(fields=['view_event', 'section_type']),
        ]

    def __str__(self):
        return (
            f'{self.view_event.diagnostic.title} — '
            f'{self.section_type} — {self.time_spent_seconds:.1f}s'
        )
