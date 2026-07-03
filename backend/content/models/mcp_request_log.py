from django.db import models


class McpRequestLog(models.Model):
    """
    Activity trail for MCP connectors, surfaced in /panel/mcps.

    Every request hitting the MCP endpoint records one event so the
    operator can see whether claude.ai actually connected and, if not,
    which error it hit — without reading server logs.
    """

    EVENT_CHOICES = [
        ('handshake', 'Handshake'),
        ('tool_call', 'Tool call'),
        ('auth_error', 'Auth error'),
        ('origin_rejected', 'Origin rejected'),
    ]

    KEEP_PER_CONNECTOR = 50

    connector = models.ForeignKey(
        'content.McpConnector',
        on_delete=models.CASCADE,
        related_name='request_logs',
    )
    event = models.CharField(max_length=20, choices=EVENT_CHOICES)
    ok = models.BooleanField(default=True)
    detail = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        verbose_name = 'MCP Request Log'
        verbose_name_plural = 'MCP Request Logs'

    def __str__(self):
        return f'{self.connector.slug} {self.event} ok={self.ok}'

    @classmethod
    def record(cls, connector, event, ok=True, detail=''):
        """Append an event and prune the trail to the newest KEEP_PER_CONNECTOR."""
        entry = cls.objects.create(
            connector=connector, event=event, ok=ok, detail=detail[:255],
        )
        stale_ids = list(
            cls.objects.filter(connector=connector)
            .values_list('id', flat=True)[cls.KEEP_PER_CONNECTOR:]
        )
        if stale_ids:
            cls.objects.filter(id__in=stale_ids).delete()
        return entry
