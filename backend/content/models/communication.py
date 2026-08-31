from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class CommunicationThread(models.Model):
    """A client conversation that can span several ordered messages."""

    class Status(models.TextChoices):
        OPEN = 'open', 'Abierto'
        CLOSED = 'closed', 'Cerrado'

    client = models.ForeignKey(
        'accounts.UserProfile',
        on_delete=models.PROTECT,
        related_name='communication_threads',
        limit_choices_to={'role': 'client'},
    )
    project = models.ForeignKey(
        'accounts.Project',
        on_delete=models.SET_NULL,
        related_name='communication_threads',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )
    last_activity_at = models.DateTimeField(default=timezone.now, db_index=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='communication_threads_created',
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='communication_threads_updated',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_activity_at', '-id']
        indexes = [
            models.Index(
                fields=['client', 'status', 'last_activity_at'],
                name='commthread_client_status_at',
            ),
            models.Index(
                fields=['project', 'status', 'last_activity_at'],
                name='commthread_project_status_at',
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        errors = {}
        if self.client_id and self.client.role != self.client.ROLE_CLIENT:
            errors['client'] = 'El perfil seleccionado no es un cliente.'
        if (
            self.client_id
            and self.project_id
            and self.project.client_id != self.client.user_id
        ):
            errors['project'] = 'El proyecto no pertenece al cliente del hilo.'
        if errors:
            raise ValidationError(errors)


class CommunicationMessage(models.Model):
    """One immutable-after-delivery entry in a client conversation."""

    class Channel(models.TextChoices):
        EMAIL = 'email', 'Correo'
        WHATSAPP = 'whatsapp', 'WhatsApp'

    class Direction(models.TextChoices):
        OUTGOING = 'outgoing', 'Saliente'
        INCOMING = 'incoming', 'Entrante'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Borrador'
        SENT = 'sent', 'Enviado'
        RECEIVED = 'received', 'Recibido'
        FAILED = 'failed', 'Fallido'

    class Source(models.TextChoices):
        MANUAL = 'manual', 'Registro manual'
        PLATFORM_EMAIL = 'platform_email', 'Correo enviado por la plataforma'
        LEGACY_EMAIL = 'legacy_email', 'Correo histórico importado'

    thread = models.ForeignKey(
        CommunicationThread,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    channel = models.CharField(max_length=12, choices=Channel.choices)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    status = models.CharField(max_length=10, choices=Status.choices)
    subject = models.CharField(max_length=500, blank=True, default='')
    content = models.TextField()
    occurred_at = models.DateTimeField(db_index=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.MANUAL,
    )
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        related_name='replies',
        null=True,
        blank=True,
    )
    email_log = models.OneToOneField(
        'content.EmailLog',
        on_delete=models.SET_NULL,
        related_name='communication_message',
        null=True,
        blank=True,
    )
    documents = models.ManyToManyField(
        'content.Document',
        through='content.CommunicationAttachment',
        related_name='communication_messages',
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='communication_messages_created',
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='communication_messages_updated',
        null=True,
        blank=True,
    )
    voided_at = models.DateTimeField(null=True, blank=True)
    void_reason = models.TextField(blank=True, default='')
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='communication_messages_voided',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['occurred_at', 'id']
        indexes = [
            models.Index(
                fields=['thread', 'occurred_at'],
                name='commmessage_thread_at',
            ),
            models.Index(
                fields=['channel', 'direction', 'status'],
                name='commmessage_route_status',
            ),
        ]

    def __str__(self):
        return f'{self.get_direction_display()} · {self.get_channel_display()}'


class CommunicationAttachment(models.Model):
    """Reference an existing Document without copying its file or content."""

    message = models.ForeignKey(
        CommunicationMessage,
        on_delete=models.CASCADE,
        related_name='attachments',
    )
    document = models.ForeignKey(
        'content.Document',
        on_delete=models.PROTECT,
        related_name='communication_attachments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['message', 'document'],
                name='unique_communication_document',
            ),
        ]

    def __str__(self):
        return f'{self.message_id} → {self.document_id}'


class CommunicationMessageRevision(models.Model):
    """Append-only audit trail for successful draft edits."""

    message = models.ForeignKey(
        CommunicationMessage,
        on_delete=models.CASCADE,
        related_name='revisions',
    )
    changes = models.JSONField(default=list)
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='communication_message_revisions',
        null=True,
        blank=True,
    )
    edited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-edited_at', '-id']
        indexes = [
            models.Index(
                fields=['message', 'edited_at'],
                name='commrevision_message_at',
            ),
        ]

    def __str__(self):
        return f'Revisión de borrador #{self.message_id}'


class CommunicationMessageDateCorrection(models.Model):
    """Append-only audit trail for corrections to a message's business date."""

    message = models.ForeignKey(
        CommunicationMessage,
        on_delete=models.CASCADE,
        related_name='date_corrections',
    )
    previous_occurred_at = models.DateTimeField()
    corrected_occurred_at = models.DateTimeField()
    reason = models.TextField()
    corrected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='communication_date_corrections',
        null=True,
        blank=True,
    )
    corrected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-corrected_at', '-id']

    def __str__(self):
        return f'Corrección de fecha #{self.message_id}'
