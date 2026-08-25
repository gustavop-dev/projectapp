import unicodedata

from django.conf import settings
from django.db import models

from content.utils import safe_slug


def normalize_document_state_name(value):
    """Return the accent/case-insensitive key used to prevent duplicates."""
    normalized = unicodedata.normalize('NFKD', str(value or '').strip())
    without_accents = ''.join(
        character for character in normalized
        if not unicodedata.combining(character)
    )
    return ' '.join(without_accents.casefold().split())


class DocumentStateGroup(models.Model):
    """A configurable group of mutually exclusive or additive states."""

    class SelectionMode(models.TextChoices):
        EXCLUSIVE = 'exclusive', 'Uno activo'
        ADDITIVE = 'additive', 'Varios activos'

    name = models.CharField(max_length=80, unique=True)
    selection_mode = models.CharField(
        max_length=12,
        choices=SelectionMode.choices,
        default=SelectionMode.ADDITIVE,
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('order', 'name')

    def __str__(self):
        return self.name


class DocumentState(models.Model):
    """User-managed document state definition.

    ``system_key`` keeps integrations stable while users remain free to rename
    seeded states. States are retired/merged instead of deleted so episodes
    always retain their original meaning.
    """

    class Color(models.TextChoices):
        GRAY = 'gray', 'Gris'
        EMERALD = 'emerald', 'Verde'
        BLUE = 'blue', 'Azul'
        YELLOW = 'yellow', 'Amarillo'
        ORANGE = 'orange', 'Naranja'
        RED = 'red', 'Rojo'
        PURPLE = 'purple', 'Morado'

    name = models.CharField(max_length=60)
    normalized_name = models.CharField(max_length=80, unique=True, editable=False)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    color = models.CharField(
        max_length=16,
        choices=Color.choices,
        default=Color.GRAY,
    )
    group = models.ForeignKey(
        DocumentStateGroup,
        on_delete=models.PROTECT,
        related_name='states',
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    system_key = models.CharField(
        max_length=40,
        unique=True,
        null=True,
        blank=True,
        help_text='Stable key for seeded integrations; names remain editable.',
    )
    merged_into = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='merged_sources',
    )
    incompatibilities = models.ManyToManyField(
        'self',
        symmetrical=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('group__order', 'order', 'name')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = ' '.join(self.name.strip().split())
        self.normalized_name = normalize_document_state_name(self.name)
        if not self.slug:
            base = safe_slug(self.name, 'estado')
            slug = base
            index = 2
            while DocumentState.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{index}'
                index += 1
            self.slug = slug
        super().save(*args, **kwargs)


class DocumentStateEpisode(models.Model):
    """One occurrence of a state during a document's lifetime."""

    class Outcome(models.TextChoices):
        COMPLETED = 'completed', 'Cerrado'
        REMOVED = 'removed', 'Quitado'
        TRANSITIONED = 'transitioned', 'Transicionado'
        MERGED = 'merged', 'Fusionado'

    class Origin(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        NOTE = 'note', 'Nota'
        EMAIL = 'email', 'Correo'
        MIGRATION = 'migration', 'Migración'
        MCP = 'mcp', 'MCP'

    document = models.ForeignKey(
        'content.Document',
        on_delete=models.CASCADE,
        related_name='state_episodes',
    )
    state = models.ForeignKey(
        DocumentState,
        on_delete=models.PROTECT,
        related_name='episodes',
    )
    opened_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    outcome = models.CharField(
        max_length=16,
        choices=Outcome.choices,
        blank=True,
        default='',
    )
    close_note = models.CharField(max_length=500, blank=True, default='')
    origin = models.CharField(
        max_length=16,
        choices=Origin.choices,
        default=Origin.MANUAL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at', '-id')
        indexes = [
            models.Index(fields=('document', 'closed_at')),
            models.Index(fields=('state', 'closed_at')),
        ]

    def __str__(self):
        return f'{self.document} — {self.state}'


class DocumentStateEpisodeEvent(models.Model):
    """Append-only audit event for an episode."""

    class EventType(models.TextChoices):
        OPENED = 'opened', 'Abierto'
        CLOSED = 'closed', 'Cerrado'
        REMOVED = 'removed', 'Quitado'
        TRANSITIONED = 'transitioned', 'Transicionado'
        MERGED = 'merged', 'Fusionado'
        OPENED_AT_CORRECTED = (
            'opened_at_corrected',
            'Fecha de apertura corregida',
        )

    episode = models.ForeignKey(
        DocumentStateEpisode,
        on_delete=models.CASCADE,
        related_name='events',
    )
    event_type = models.CharField(max_length=24, choices=EventType.choices)
    effective_at = models.DateTimeField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ('-recorded_at', '-id')
        indexes = [models.Index(fields=('episode', 'recorded_at'))]

    def __str__(self):
        return f'{self.episode_id} — {self.event_type}'
