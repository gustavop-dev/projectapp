import uuid

from django.db import models


class McpActionIntent(models.Model):
    """Short-lived, single-use confirmation for a sensitive MCP action."""

    STATUS_PENDING = 'pending'
    STATUS_EXECUTED = 'executed'
    STATUS_EXPIRED = 'expired'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_EXECUTED, 'Executed'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    connector = models.ForeignKey(
        'content.McpConnector',
        on_delete=models.CASCADE,
        related_name='action_intents',
    )
    credential = models.ForeignKey(
        'content.McpCredential',
        on_delete=models.CASCADE,
        related_name='action_intents',
    )
    tool_name = models.CharField(max_length=120)
    arguments = models.JSONField(default=dict)
    arguments_hash = models.CharField(max_length=64)
    impact = models.JSONField(default=dict, blank=True)
    resource_etags = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    expires_at = models.DateTimeField(db_index=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['credential', 'status', 'expires_at'],
                name='mcp_intent_cred_status_idx',
            ),
        ]

    def __str__(self):
        return f'{self.connector.slug}:{self.tool_name}:{self.status}'
