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
        ('discovery', 'Discovery'),
        ('tool_call', 'Tool call'),
        ('auth_error', 'Auth error'),
        ('origin_rejected', 'Origin rejected'),
    ]

    RISK_CHOICES = [
        ('read', 'Read'),
        ('write', 'Reversible write'),
        ('sensitive', 'Sensitive'),
    ]

    KEEP_PER_CONNECTOR = 200

    connector = models.ForeignKey(
        'content.McpConnector',
        on_delete=models.CASCADE,
        related_name='request_logs',
    )
    credential = models.ForeignKey(
        'content.McpCredential',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='request_logs',
    )
    request_id = models.CharField(max_length=36, blank=True, default='', db_index=True)
    event = models.CharField(max_length=20, choices=EVENT_CHOICES)
    ok = models.BooleanField(default=True)
    detail = models.CharField(max_length=255, blank=True, default='')
    tool_name = models.CharField(max_length=120, blank=True, default='')
    risk_level = models.CharField(
        max_length=12,
        choices=RISK_CHOICES,
        blank=True,
        default='',
    )
    error_code = models.CharField(max_length=64, blank=True, default='')
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    object_refs = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        verbose_name = 'MCP Request Log'
        verbose_name_plural = 'MCP Request Logs'

    def __str__(self):
        return f'{self.connector.slug} {self.event} ok={self.ok}'

    @classmethod
    def record(
        cls,
        connector,
        event,
        ok=True,
        detail='',
        *,
        credential=None,
        request_id='',
        tool_name='',
        risk_level='',
        error_code='',
        duration_ms=None,
        object_refs=None,
    ):
        """Append an event and prune the trail to the newest KEEP_PER_CONNECTOR."""
        entry = cls.objects.create(
            connector=connector,
            credential=credential,
            request_id=request_id,
            event=event,
            ok=ok,
            detail=detail[:255],
            tool_name=tool_name[:120],
            risk_level=risk_level,
            error_code=error_code[:64],
            duration_ms=duration_ms,
            object_refs=object_refs or [],
        )
        stale_ids = list(
            cls.objects.filter(connector=connector)
            .values_list('id', flat=True)[cls.KEEP_PER_CONNECTOR:]
        )
        if stale_ids:
            cls.objects.filter(id__in=stale_ids).delete()
        return entry
