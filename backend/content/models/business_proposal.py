import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class BusinessProposal(models.Model):
    """
    Core model for business proposals sent to prospective clients.

    Each proposal has a UUID for public access, an expiration date,
    and tracks client interactions (views, reminder emails).
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SENT = 'sent', 'Sent'
        VIEWED = 'viewed', 'Viewed'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        NEGOTIATING = 'negotiating', 'Negotiating'
        EXPIRED = 'expired', 'Expired'

    class Currency(models.TextChoices):
        COP = 'COP', 'COP'
        USD = 'USD', 'USD'

    class Language(models.TextChoices):
        ES = 'es', 'Español'
        EN = 'en', 'English'

    # Identity
    uuid = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False, db_index=True
    )
    title = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255)
    client_email = models.EmailField(blank=True)
    slug = models.SlugField(max_length=255, blank=True)

    # Language
    language = models.CharField(
        max_length=2, choices=Language.choices, default=Language.ES
    )

    # Financial
    total_investment = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    currency = models.CharField(
        max_length=3, choices=Currency.choices, default=Currency.COP
    )
    hosting_percent = models.PositiveIntegerField(
        default=30,
        help_text='Percentage of total investment charged for annual hosting.',
    )

    # Status & lifecycle
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    reminder_days = models.PositiveIntegerField(default=10)
    urgency_reminder_days = models.PositiveIntegerField(default=15)
    discount_percent = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    automations_paused = models.BooleanField(
        default=False,
        help_text='When true, no automatic emails (reminder, urgency, inactivity) are sent for this proposal.',
    )
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    urgency_email_sent_at = models.DateTimeField(null=True, blank=True)

    # Classification
    PROJECT_TYPE_CHOICES = [
        ('website', 'Sitio Web'),
        ('ecommerce', 'E-commerce'),
        ('webapp', 'Aplicación Web'),
        ('landing', 'Landing Page'),
        ('redesign', 'Rediseño'),
        ('other', 'Otro'),
    ]
    MARKET_TYPE_CHOICES = [
        ('b2b', 'B2B'),
        ('b2c', 'B2C'),
        ('saas', 'SaaS'),
        ('retail', 'Retail'),
        ('services', 'Servicios profesionales'),
        ('health', 'Salud'),
        ('education', 'Educación'),
        ('real_estate', 'Inmobiliaria'),
        ('other', 'Otro'),
    ]
    project_type = models.CharField(
        max_length=20, choices=PROJECT_TYPE_CHOICES, blank=True, default=''
    )
    market_type = models.CharField(
        max_length=20, choices=MARKET_TYPE_CHOICES, blank=True, default=''
    )
    project_type_custom = models.CharField(
        max_length=100, blank=True, default='',
        help_text='Free-text description when project_type is "other".'
    )
    market_type_custom = models.CharField(
        max_length=100, blank=True, default='',
        help_text='Free-text description when market_type is "other".'
    )
    client_phone = models.CharField(max_length=30, blank=True, default='')

    # Rejection feedback
    rejection_reason = models.CharField(max_length=100, blank=True, default='')
    rejection_comment = models.TextField(blank=True, default='')

    # Tracking
    last_activity_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    first_viewed_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    revisit_alert_sent_at = models.DateTimeField(null=True, blank=True)
    abandonment_email_sent_at = models.DateTimeField(null=True, blank=True)
    investment_interest_email_sent_at = models.DateTimeField(null=True, blank=True)
    followup_scheduled_at = models.DateTimeField(null=True, blank=True)
    stakeholder_alert_sent_at = models.DateTimeField(null=True, blank=True)
    post_expiration_alert_sent_at = models.DateTimeField(null=True, blank=True)
    calculator_followup_sent_at = models.DateTimeField(null=True, blank=True)

    # Engagement signals
    engagement_declining = models.BooleanField(
        default=False,
        help_text='Set when engagement decay is detected; reset on normal session.',
    )
    cached_heat_score = models.PositiveSmallIntegerField(
        default=0,
        help_text='Pre-computed heat score (1-10), updated by tracking endpoint and periodic task.',
    )
    last_automated_email_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Timestamp of the last automated email sent to the client. Used for 24h cooldown.',
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Business Proposal'
        verbose_name_plural = 'Business Proposals'

    def __str__(self):
        return f'{self.title} — {self.client_name}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.client_name)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if the proposal has expired by status or date."""
        if self.status == self.Status.EXPIRED:
            return True
        if self.expires_at and self.expires_at < timezone.now():
            return True
        return False

    @property
    def days_remaining(self):
        """Return the number of days until expiration, or None if no expiry."""
        if not self.expires_at:
            return None
        delta = (self.expires_at - timezone.now()).days
        return max(delta, 0)

    @property
    def public_url(self):
        """Build the client-facing URL for viewing this proposal."""
        base = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000')
        return f'{base}/proposal/{self.uuid}'


class ProposalAlert(models.Model):
    """
    Manual alert/reminder created by sellers for a specific proposal.

    Complements the automatic alerts (not_viewed, not_responded, expiring_soon)
    with seller-defined reminders that appear in the proposals dashboard.
    """

    ALERT_TYPE_CHOICES = [
        ('reminder', 'Recordatorio'),
        ('followup', 'Seguimiento'),
        ('call', 'Llamada'),
        ('meeting', 'Reunión'),
        ('custom', 'Personalizado'),
        ('discount_suggestion', 'Sugerencia de descuento'),
        ('post_expiration_visit', 'Visita post-expiración'),
        ('high_engagement_today', 'Alta actividad hoy'),
        ('whatsapp_suggestion', 'Sugerencia de WhatsApp'),
        ('calculator_followup', 'Seguimiento calculadora'),
        ('engagement_decay', 'Pérdida de engagement'),
        ('post_rejection_revisit', 'Revisita post-rechazo'),
    ]

    proposal = models.ForeignKey(
        BusinessProposal,
        on_delete=models.CASCADE,
        related_name='manual_alerts',
    )
    alert_type = models.CharField(
        max_length=30, choices=ALERT_TYPE_CHOICES, default='reminder'
    )
    message = models.CharField(max_length=500)
    alert_date = models.DateTimeField(
        help_text='When this alert should become visible.'
    )
    PRIORITY_CHOICES = [
        ('critical', 'Alta urgencia'),
        ('high', 'Alta'),
        ('normal', 'Normal'),
    ]
    PRIORITY_BY_TYPE = {
        'engagement_decay': 'critical',
        'post_expiration_visit': 'critical',
        'post_rejection_revisit': 'critical',
        'discount_suggestion': 'high',
        'high_engagement_today': 'high',
        'calculator_followup': 'high',
        'whatsapp_suggestion': 'high',
    }
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default='normal',
        help_text='Auto-computed priority based on alert type.',
    )
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.priority or self.priority == 'normal':
            self.priority = self.PRIORITY_BY_TYPE.get(self.alert_type, 'normal')
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Proposal Alert'
        verbose_name_plural = 'Proposal Alerts'

    def __str__(self):
        return f'Alert: {self.proposal.client_name} — {self.message[:50]}'
