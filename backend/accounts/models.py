import secrets
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from accounts.services.image_utils import optimize_avatar, optimize_image


class UserProfileQuerySet(models.QuerySet):
    def clients(self):
        return self.filter(role=UserProfile.ROLE_CLIENT).select_related('user')

    def admins(self):
        return self.filter(role=UserProfile.ROLE_ADMIN).select_related('user')


class UserProfileManager(models.Manager.from_queryset(UserProfileQuerySet)):
    pass


class UserProfile(models.Model):
    """
    Extends auth.User with platform-specific fields.
    One-to-one relationship to avoid changing AUTH_USER_MODEL.
    """

    ROLE_ADMIN = 'admin'
    ROLE_CLIENT = 'client'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_CLIENT, 'Client'),
    ]

    PLACEHOLDER_EMAIL_DOMAIN = '@temp.example.com'

    GENDER_MALE = 'male'
    GENDER_FEMALE = 'female'
    GENDER_OTHER = 'other'
    GENDER_PREFER_NOT = 'prefer_not_to_say'
    GENDER_CHOICES = [
        (GENDER_MALE, 'Masculino'),
        (GENDER_FEMALE, 'Femenino'),
        (GENDER_OTHER, 'Otro'),
        (GENDER_PREFER_NOT, 'Prefiero no decir'),
    ]

    EDUCATION_PRIMARY = 'primaria'
    EDUCATION_SECONDARY = 'secundaria'
    EDUCATION_TECHNICAL = 'tecnico'
    EDUCATION_UNIVERSITY = 'universitario'
    EDUCATION_POSTGRADUATE = 'posgrado'
    EDUCATION_OTHER = 'otro'
    EDUCATION_CHOICES = [
        (EDUCATION_PRIMARY, 'Primaria'),
        (EDUCATION_SECONDARY, 'Secundaria'),
        (EDUCATION_TECHNICAL, 'Técnico'),
        (EDUCATION_UNIVERSITY, 'Universitario'),
        (EDUCATION_POSTGRADUATE, 'Posgrado'),
        (EDUCATION_OTHER, 'Otro'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_CLIENT)
    is_onboarded = models.BooleanField(
        default=False,
        help_text='True after the client sets their own password.',
    )
    company_name = models.CharField(max_length=200, blank=True, default='')
    phone = models.CharField(max_length=30, blank=True, default='')
    cedula = models.CharField(max_length=20, blank=True, default='')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=20, choices=GENDER_CHOICES, blank=True, default='',
    )
    education_level = models.CharField(
        max_length=20, choices=EDUCATION_CHOICES, blank=True, default='',
    )
    avatar = models.ImageField(
        upload_to='avatars/', null=True, blank=True,
        help_text='Optimized automatically on upload.',
    )
    avatar_url = models.URLField(
        max_length=500, blank=True, default='',
        help_text='Deprecated — use avatar ImageField instead.',
    )
    theme_color = models.CharField(
        max_length=7, blank=True, default='',
        help_text='Hex color for UI theme (e.g. #002921).',
    )
    cover_image = models.CharField(
        max_length=300, blank=True, default='',
        help_text='Path to cover gallery image (e.g. NASA Archive/imgi_21_nasa_the_blue_marble.jpg).',
    )
    custom_cover_image = models.ImageField(
        upload_to='covers/', null=True, blank=True,
        help_text='User-uploaded custom cover image.',
    )
    profile_completed = models.BooleanField(
        default=False,
        help_text='True after the client fills in their profile details.',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_profiles',
        help_text='Admin who created this client account.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserProfileManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_client(self):
        return self.role == self.ROLE_CLIENT

    @property
    def is_email_placeholder(self):
        """True when the linked user's email is a generated temp placeholder."""
        return (self.user.email or '').endswith(self.PLACEHOLDER_EMAIL_DOMAIN)

    @property
    def avatar_display_url(self):
        """Return the best available avatar URL."""
        if self.avatar:
            return self.avatar.url
        return self.avatar_url or ''

    def save(self, *args, **kwargs):
        if self.avatar and hasattr(self.avatar.file, 'content_type'):
            content_type = getattr(self.avatar.file, 'content_type', '')
            if content_type and content_type.startswith('image/'):
                try:
                    self.avatar = optimize_avatar(self.avatar)
                except Exception:
                    pass
        super().save(*args, **kwargs)


def _user_role(self):
    profile = getattr(self, 'profile', None)
    return profile.role if profile else None


def _user_is_client_role(self):
    profile = getattr(self, 'profile', None)
    return bool(profile and profile.is_client)


def _user_is_admin_role(self):
    profile = getattr(self, 'profile', None)
    return bool(profile and profile.is_admin)


_AuthUser = get_user_model()
_AuthUser.add_to_class('role', property(_user_role))
_AuthUser.add_to_class('is_client_role', property(_user_is_client_role))
_AuthUser.add_to_class('is_admin_role', property(_user_is_admin_role))


class VerificationCode(models.Model):
    """
    Time-limited OTP for onboarding verification and password resets.
    """

    PURPOSE_ONBOARDING = 'onboarding'
    PURPOSE_PASSWORD_RESET = 'password_reset'
    PURPOSE_CHOICES = [
        (PURPOSE_ONBOARDING, 'Onboarding'),
        (PURPOSE_PASSWORD_RESET, 'Password Reset'),
    ]

    MAX_ATTEMPTS = 5
    EXPIRY_MINUTES = 10

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='verification_codes',
    )
    code = models.CharField(max_length=6)
    purpose = models.CharField(
        max_length=20,
        choices=PURPOSE_CHOICES,
        default=PURPOSE_ONBOARDING,
    )
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'OTP for {self.user.email} ({self.purpose}) — {"used" if self.is_used else "active"}'

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired and self.attempts < self.MAX_ATTEMPTS

    def increment_attempts(self):
        self.attempts += 1
        self.save(update_fields=['attempts'])

    def mark_used(self):
        self.is_used = True
        self.save(update_fields=['is_used'])

    @classmethod
    def generate_code(cls):
        return ''.join(secrets.choice(string.digits) for _ in range(6))

    @classmethod
    def create_for_user(cls, user, purpose=PURPOSE_ONBOARDING):
        """Invalidate previous codes and create a new one."""
        cls.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)
        return cls.objects.create(
            user=user,
            code=cls.generate_code(),
            purpose=purpose,
            expires_at=timezone.now() + timezone.timedelta(minutes=cls.EXPIRY_MINUTES),
        )


class Project(models.Model):
    """
    A client project managed through the platform.
    Each project belongs to a single client (User with client role).
    """

    STATUS_ACTIVE = 'active'
    STATUS_PAUSED = 'paused'
    STATUS_COMPLETED = 'completed'
    STATUS_ARCHIVED = 'archived'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Activo'),
        (STATUS_PAUSED, 'Pausado'),
        (STATUS_COMPLETED, 'Completado'),
        (STATUS_ARCHIVED, 'Archivado'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects',
        help_text='The client user this project belongs to.',
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE,
    )
    progress = models.PositiveIntegerField(
        default=0,
        help_text='Overall progress percentage (0-100).',
    )
    start_date = models.DateField(null=True, blank=True)
    estimated_end_date = models.DateField(null=True, blank=True)
    payment_milestones = models.JSONField(
        default=list, blank=True,
        help_text='Development payment milestones from proposal section 4 (admin-visible only).',
    )
    hosting_tiers = models.JSONField(
        default=list, blank=True,
        help_text='Hosting billing tiers from proposal (semiannual/quarterly/monthly with pricing).',
    )
    hosting_start_date = models.DateField(
        null=True, blank=True,
        help_text='Date when hosting billing should begin (set by admin).',
    )

    # Quick-access URLs (admin-only visibility in the API)
    production_url = models.URLField(max_length=500, blank=True, default='')
    staging_url = models.URLField(max_length=500, blank=True, default='')
    admin_url = models.URLField(max_length=500, blank=True, default='')
    repository_url = models.URLField(max_length=500, blank=True, default='')

    # Django admin credentials for the project's own site. The password is stored
    # as a Fernet ciphertext; see accounts/services/credential_cipher.py.
    admin_username = models.CharField(max_length=150, blank=True, default='')
    admin_password_encrypted = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.name} — {self.client.email}'

    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def linked_business_proposal(self):
        """First BusinessProposal linked via a deliverable on this project (hosting/PDFs)."""
        from content.models import BusinessProposal

        return (
            BusinessProposal.objects.filter(deliverable__project_id=self.id)
            .select_related('deliverable')
            .order_by('deliverable_id')
            .first()
        )


class Requirement(models.Model):
    """
    A single requirement (card) on the project Kanban board.
    """

    STATUS_BACKLOG = 'backlog'
    STATUS_TODO = 'todo'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_IN_REVIEW = 'in_review'
    STATUS_APPROVAL = 'approval'
    STATUS_DONE = 'done'
    STATUS_CHOICES = [
        (STATUS_BACKLOG, 'Backlog'),
        (STATUS_TODO, 'To do'),
        (STATUS_IN_PROGRESS, 'In progress'),
        (STATUS_IN_REVIEW, 'In review'),
        (STATUS_APPROVAL, 'Aprobación'),
        (STATUS_DONE, 'Done'),
    ]

    PRIORITY_CRITICAL = 'critical'
    PRIORITY_HIGH = 'high'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_LOW = 'low'
    PRIORITY_CHOICES = [
        (PRIORITY_CRITICAL, 'Crítica'),
        (PRIORITY_HIGH, 'Alta'),
        (PRIORITY_MEDIUM, 'Media'),
        (PRIORITY_LOW, 'Baja'),
    ]

    deliverable = models.ForeignKey(
        'Deliverable', on_delete=models.CASCADE, related_name='requirements',
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_BACKLOG,
    )
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM,
    )
    configuration = models.TextField(
        blank=True, default='',
        help_text='Role/privilege context for this requirement (e.g. "Only for admin role").',
    )
    flow = models.TextField(
        blank=True, default='',
        help_text='User flow description within the software for this requirement.',
    )
    order = models.PositiveIntegerField(
        default=0, help_text='Sort order within the column.',
    )
    source_epic_key = models.CharField(max_length=200, blank=True, default='', db_index=True)
    source_epic_title = models.CharField(max_length=300, blank=True, default='')
    source_flow_key = models.CharField(max_length=200, blank=True, default='', db_index=True)
    synced_from_proposal = models.BooleanField(default=False)
    is_archived = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Hidden from default lists; row kept for audit.',
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['deliverable', 'source_flow_key'],
                condition=~models.Q(source_flow_key=''),
                name='uniq_requirement_deliverable_flow_key',
            ),
        ]

    def __str__(self):
        return f'{self.title} [{self.get_status_display()}]'

    @property
    def project(self):
        return self.deliverable.project

    @property
    def project_id(self):
        return self.deliverable.project_id


class RequirementComment(models.Model):
    """Comment on a requirement card — can be internal (admin-only) or public."""

    requirement = models.ForeignKey(
        Requirement, on_delete=models.CASCADE, related_name='comments',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requirement_comments',
    )
    content = models.TextField()
    is_internal = models.BooleanField(
        default=False, help_text='Internal comments are visible only to admins.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.user.email} on {self.requirement_id}'


class RequirementHistory(models.Model):
    """Tracks status changes of a requirement."""

    requirement = models.ForeignKey(
        Requirement, on_delete=models.CASCADE, related_name='history',
    )
    from_status = models.CharField(max_length=20, choices=Requirement.STATUS_CHOICES)
    to_status = models.CharField(max_length=20, choices=Requirement.STATUS_CHOICES)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.from_status} → {self.to_status}'


class ChangeRequest(models.Model):
    """
    A client-initiated change request for a project.
    The admin evaluates and responds with estimated cost/time.
    """

    STATUS_PENDING = 'pending'
    STATUS_EVALUATING = 'evaluating'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_NEEDS_CLARIFICATION = 'needs_clarification'
    STATUS_OUT_OF_SCOPE = 'out_of_scope'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_EVALUATING, 'En evaluación'),
        (STATUS_APPROVED, 'Aprobada'),
        (STATUS_REJECTED, 'Rechazada'),
        (STATUS_NEEDS_CLARIFICATION, 'Requiere aclaración'),
        (STATUS_OUT_OF_SCOPE, 'Fuera de alcance'),
    ]

    PRIORITY_CRITICAL = 'critical'
    PRIORITY_HIGH = 'high'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_LOW = 'low'
    PRIORITY_CHOICES = [
        (PRIORITY_CRITICAL, 'Crítica'),
        (PRIORITY_HIGH, 'Alta'),
        (PRIORITY_MEDIUM, 'Media'),
        (PRIORITY_LOW, 'Baja'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='change_requests',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='change_requests',
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default='')
    module_or_screen = models.CharField(max_length=200, blank=True, default='')
    suggested_priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM,
    )
    is_urgent = models.BooleanField(default=False)
    status = models.CharField(
        max_length=25, choices=STATUS_CHOICES, default=STATUS_PENDING,
    )
    admin_response = models.TextField(blank=True, default='')
    estimated_cost = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='Estimated additional cost in project currency.',
    )
    estimated_time = models.CharField(
        max_length=100, blank=True, default='',
        help_text='Estimated time to implement (e.g. "2 semanas").',
    )
    linked_requirement = models.ForeignKey(
        Requirement, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='source_change_request',
        help_text='Requirement created from this change request.',
    )
    screenshot = models.ImageField(
        upload_to='change_requests/', null=True, blank=True,
        help_text='Optimized automatically on upload (WhatsApp-like compression).',
    )
    is_archived = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Hidden from default lists; row kept for audit.',
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} [{self.get_status_display()}]'

    def save(self, *args, **kwargs):
        if self.screenshot and hasattr(self.screenshot.file, 'content_type'):
            content_type = getattr(self.screenshot.file, 'content_type', '')
            if content_type and content_type.startswith('image/'):
                try:
                    self.screenshot = optimize_image(self.screenshot, field_name='screenshot')
                except Exception:
                    pass
        super().save(*args, **kwargs)


class ChangeRequestComment(models.Model):
    """Comment thread on a change request. Supports internal (admin-only) comments."""

    change_request = models.ForeignKey(
        ChangeRequest, on_delete=models.CASCADE, related_name='comments',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='change_request_comments',
    )
    content = models.TextField()
    is_internal = models.BooleanField(
        default=False, help_text='Internal comments are visible only to admins.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.user.email} on CR #{self.change_request_id}'


class BugReport(models.Model):
    """
    A bug report filed for a specific project deliverable (epic/scope).
    Admin manages the lifecycle: confirm, fix, QA, resolve.
    """

    SEVERITY_CRITICAL = 'critical'
    SEVERITY_HIGH = 'high'
    SEVERITY_MEDIUM = 'medium'
    SEVERITY_LOW = 'low'
    SEVERITY_CHOICES = [
        (SEVERITY_CRITICAL, 'Crítica'),
        (SEVERITY_HIGH, 'Alta'),
        (SEVERITY_MEDIUM, 'Media'),
        (SEVERITY_LOW, 'Baja'),
    ]

    STATUS_REPORTED = 'reported'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_FIXING = 'fixing'
    STATUS_QA = 'qa'
    STATUS_RESOLVED = 'resolved'
    STATUS_NOT_REPRODUCIBLE = 'not_reproducible'
    STATUS_WONT_FIX = 'wont_fix'
    STATUS_DUPLICATE = 'duplicate'
    STATUS_CHOICES = [
        (STATUS_REPORTED, 'Reportado'),
        (STATUS_CONFIRMED, 'Confirmado'),
        (STATUS_FIXING, 'En corrección'),
        (STATUS_QA, 'En QA'),
        (STATUS_RESOLVED, 'Resuelto'),
        (STATUS_NOT_REPRODUCIBLE, 'No reproducible'),
        (STATUS_WONT_FIX, 'No se corregirá'),
        (STATUS_DUPLICATE, 'Duplicado'),
    ]

    ENV_PRODUCTION = 'production'
    ENV_STAGING = 'staging'
    ENV_DEV = 'dev'
    ENV_CHOICES = [
        (ENV_PRODUCTION, 'Producción'),
        (ENV_STAGING, 'Staging'),
        (ENV_DEV, 'Desarrollo'),
    ]

    deliverable = models.ForeignKey(
        'Deliverable', on_delete=models.CASCADE, related_name='bug_reports',
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bug_reports',
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default='')
    severity = models.CharField(
        max_length=20, choices=SEVERITY_CHOICES, default=SEVERITY_MEDIUM,
    )
    steps_to_reproduce = models.JSONField(
        default=list, blank=True,
        help_text='Numbered list of steps to reproduce the bug.',
    )
    expected_behavior = models.TextField(blank=True, default='')
    actual_behavior = models.TextField(blank=True, default='')
    environment = models.CharField(
        max_length=20, choices=ENV_CHOICES, default=ENV_PRODUCTION,
    )
    device_browser = models.CharField(max_length=200, blank=True, default='')
    is_recurring = models.BooleanField(default=False)
    status = models.CharField(
        max_length=25, choices=STATUS_CHOICES, default=STATUS_REPORTED,
    )
    admin_response = models.TextField(blank=True, default='')
    linked_bug = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='duplicates',
        help_text='Original bug if this is a duplicate.',
    )
    screenshot = models.ImageField(
        upload_to='bug_reports/', null=True, blank=True,
        help_text='Optimized automatically on upload (WhatsApp-like compression).',
    )
    is_archived = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Hidden from default lists; row kept for audit.',
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} [{self.get_status_display()}]'

    def save(self, *args, **kwargs):
        if self.screenshot and hasattr(self.screenshot.file, 'content_type'):
            content_type = getattr(self.screenshot.file, 'content_type', '')
            if content_type and content_type.startswith('image/'):
                try:
                    self.screenshot = optimize_image(self.screenshot, field_name='screenshot')
                except Exception:
                    pass
        super().save(*args, **kwargs)


class BugComment(models.Model):
    """Comment thread on a bug report. Supports internal (admin-only) comments."""

    bug_report = models.ForeignKey(
        BugReport, on_delete=models.CASCADE, related_name='comments',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='bug_comments',
    )
    content = models.TextField()
    is_internal = models.BooleanField(
        default=False, help_text='Internal comments are visible only to admins.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.user.email} on Bug #{self.bug_report_id}'


class Deliverable(models.Model):
    """
    A file deliverable for a project, organized by category.
    Admin uploads, client downloads. Supports version history.
    Optional file for logical rows (e.g. epic scope / linked business proposal).
    """

    CATEGORY_DESIGNS = 'designs'
    CATEGORY_CREDENTIALS = 'credentials'
    CATEGORY_DOCUMENTS = 'documents'
    CATEGORY_APKS = 'apks'
    CATEGORY_CONTRACT = 'contract'
    CATEGORY_AMENDMENT = 'amendment'
    CATEGORY_LEGAL_ANNEX = 'legal_annex'
    CATEGORY_OTHER = 'other'
    CATEGORY_CHOICES = [
        (CATEGORY_DESIGNS, 'Diseños'),
        (CATEGORY_CREDENTIALS, 'Credenciales'),
        (CATEGORY_DOCUMENTS, 'Documentos'),
        (CATEGORY_APKS, 'APKs / Builds'),
        (CATEGORY_CONTRACT, 'Contrato'),
        (CATEGORY_AMENDMENT, 'Otrosí'),
        (CATEGORY_LEGAL_ANNEX, 'Anexo legal'),
        (CATEGORY_OTHER, 'Otros'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='deliverables',
    )
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER,
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default='')
    source_epic_key = models.CharField(max_length=200, blank=True, default='', db_index=True)
    source_epic_title = models.CharField(max_length=300, blank=True, default='')
    file = models.FileField(upload_to='deliverables/', blank=True, null=True)
    current_version = models.PositiveIntegerField(default=1)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='uploaded_deliverables',
    )
    is_archived = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Hidden from default lists; row kept for audit.',
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', '-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'source_epic_key'],
                condition=~models.Q(source_epic_key=''),
                name='uniq_deliverable_project_epic_key',
            ),
        ]

    def __str__(self):
        return f'{self.title} v{self.current_version} [{self.get_category_display()}]'

    @property
    def file_name(self):
        if self.file:
            return self.file.name.split('/')[-1]
        return ''

    @property
    def file_size(self):
        try:
            return self.file.size
        except Exception:
            return 0


class DataModelEntity(models.Model):
    """
    A data model entity synced from the BusinessProposal technical document.
    One copy per deliverable (FK).
    """

    deliverable = models.ForeignKey(
        Deliverable, on_delete=models.CASCADE, related_name='data_model_entities',
    )
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True, default='')
    key_fields = models.TextField(
        blank=True, default='',
        help_text='Comma-separated key fields for this entity.',
    )
    source_entity_name = models.CharField(
        max_length=300, blank=True, default='', db_index=True,
        help_text='Original entity name from proposal JSON, used for idempotent sync.',
    )
    synced_from_proposal = models.BooleanField(default=False)
    is_archived = models.BooleanField(
        default=False, db_index=True,
        help_text='Hidden from default lists; row kept for audit.',
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['deliverable', 'source_entity_name'],
                condition=~models.Q(source_entity_name=''),
                name='uniq_data_model_entity_deliverable_source',
            ),
        ]

    def __str__(self):
        return f'{self.name} (deliverable={self.deliverable_id})'


class ProjectDataModelEntity(models.Model):
    """
    A data-model entity defined at the project level via admin JSON upload.
    Reflects the actual/real state of the project's data model.
    Separate from DataModelEntity (deliverable-scoped, proposal-synced).
    """

    project = models.ForeignKey(
        'Project', on_delete=models.CASCADE,
        related_name='project_data_model_entities',
    )
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True, default='')
    key_fields = models.TextField(
        blank=True, default='',
        help_text='Comma-separated key fields for this entity.',
    )
    relationship = models.CharField(
        max_length=500, blank=True, default='',
        help_text='Relationship description (e.g. "1:N with Order").',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} (project={self.project_id})'


class DeliverableVersion(models.Model):
    """Historical version of a deliverable file."""

    deliverable = models.ForeignKey(
        Deliverable, on_delete=models.CASCADE, related_name='versions',
    )
    file = models.FileField(upload_to='deliverables/versions/')
    version_number = models.PositiveIntegerField()
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='deliverable_versions',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']

    def __str__(self):
        return f'{self.deliverable.title} v{self.version_number}'

    @property
    def file_name(self):
        if self.file:
            return self.file.name.split('/')[-1]
        return ''

    @property
    def file_size(self):
        try:
            return self.file.size
        except Exception:
            return 0


class DeliverableFile(models.Model):
    """Additional file attached to a deliverable (contract, annex, etc.)."""

    deliverable = models.ForeignKey(
        Deliverable, on_delete=models.CASCADE, related_name='attachment_files',
    )
    file = models.FileField(upload_to='deliverables/attachments/')
    title = models.CharField(max_length=300, blank=True, default='')
    category = models.CharField(
        max_length=20, choices=Deliverable.CATEGORY_CHOICES, default=Deliverable.CATEGORY_OTHER,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='deliverable_attachment_files',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.deliverable.title} — {self.title or self.file_name}'

    @property
    def file_name(self):
        if self.file:
            return self.file.name.split('/')[-1]
        return ''


class DeliverableClientFolder(models.Model):
    """Optional folder label for client-uploaded PDFs on a deliverable."""

    deliverable = models.ForeignKey(
        Deliverable, on_delete=models.CASCADE, related_name='client_folders',
    )
    name = models.CharField(max_length=200)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='deliverable_client_folders',
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.deliverable_id} — {self.name}'


class DeliverableClientUpload(models.Model):
    """PDF uploaded by the client (or admin) under a deliverable, optionally in a folder."""

    deliverable = models.ForeignKey(
        Deliverable, on_delete=models.CASCADE, related_name='client_uploads',
    )
    folder = models.ForeignKey(
        DeliverableClientFolder, on_delete=models.CASCADE,
        null=True, blank=True, related_name='uploads',
    )
    file = models.FileField(upload_to='deliverables/client_uploads/')
    title = models.CharField(max_length=300, blank=True, default='')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='deliverable_client_uploads',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.deliverable_id} — {self.title or self.file_name}'

    @property
    def file_name(self):
        if self.file:
            return self.file.name.split('/')[-1]
        return ''


class Notification(models.Model):
    """
    In-app notification for platform users.
    Created by the notification service when relevant events occur.
    """

    TYPE_BUG_REPORTED = 'bug_reported'
    TYPE_BUG_STATUS_CHANGED = 'bug_status_changed'
    TYPE_CR_CREATED = 'cr_created'
    TYPE_CR_STATUS_CHANGED = 'cr_status_changed'
    TYPE_CR_CONVERTED = 'cr_converted'
    TYPE_REQUIREMENT_MOVED = 'requirement_moved'
    TYPE_REQUIREMENT_APPROVED = 'requirement_approved'
    TYPE_DELIVERABLE_UPLOADED = 'deliverable_uploaded'
    TYPE_DELIVERABLE_NEW_VERSION = 'deliverable_new_version'
    TYPE_COMMENT_ADDED = 'comment_added'
    TYPE_GENERAL = 'general'
    TYPE_CHOICES = [
        (TYPE_BUG_REPORTED, 'Bug reportado'),
        (TYPE_BUG_STATUS_CHANGED, 'Estado de bug actualizado'),
        (TYPE_CR_CREATED, 'Solicitud de cambio creada'),
        (TYPE_CR_STATUS_CHANGED, 'Solicitud de cambio actualizada'),
        (TYPE_CR_CONVERTED, 'Solicitud convertida en requerimiento'),
        (TYPE_REQUIREMENT_MOVED, 'Requerimiento movido'),
        (TYPE_REQUIREMENT_APPROVED, 'Requerimiento aprobado'),
        (TYPE_DELIVERABLE_UPLOADED, 'Entregable subido'),
        (TYPE_DELIVERABLE_NEW_VERSION, 'Nueva versión de entregable'),
        (TYPE_COMMENT_ADDED, 'Nuevo comentario'),
        (TYPE_GENERAL, 'General'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications',
    )
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_GENERAL)
    title = models.CharField(max_length=300)
    message = models.TextField(blank=True, default='')
    related_object_type = models.CharField(
        max_length=50, blank=True, default='',
        help_text='Model name: project, change_request, bug_report, deliverable, requirement',
    )
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, null=True, blank=True,
        related_name='notifications',
        help_text='Project context for deep-linking.',
    )
    deliverable = models.ForeignKey(
        'Deliverable', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notifications',
        help_text='Deliverable context for deep-linking when applicable.',
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_type_display()}] {self.title} → {self.user.email}'


class HostingSubscription(models.Model):
    """
    Recurring hosting subscription for a project.
    Derived from the linked BusinessProposal pricing or set manually.
    """

    PLAN_MONTHLY = 'monthly'
    PLAN_QUARTERLY = 'quarterly'
    PLAN_SEMIANNUAL = 'semiannual'
    PLAN_CHOICES = [
        (PLAN_MONTHLY, 'Mensual'),
        (PLAN_QUARTERLY, 'Trimestral'),
        (PLAN_SEMIANNUAL, 'Semestral'),
    ]

    STATUS_ACTIVE = 'active'
    STATUS_SUSPENDED = 'suspended'
    STATUS_CANCELLED = 'cancelled'
    STATUS_PENDING = 'pending'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Activa'),
        (STATUS_SUSPENDED, 'Suspendida'),
        (STATUS_CANCELLED, 'Cancelada'),
        (STATUS_PENDING, 'Pendiente'),
    ]

    PLAN_MONTHS = {
        PLAN_MONTHLY: 1,
        PLAN_QUARTERLY: 3,
        PLAN_SEMIANNUAL: 6,
    }

    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name='hosting_subscription',
    )
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_MONTHLY)
    base_monthly_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Monthly hosting cost before discount (COP).',
    )
    discount_percent = models.PositiveIntegerField(
        default=0, help_text='Discount % based on plan (0, 10, 20).',
    )
    effective_monthly_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Monthly cost after discount (COP).',
    )
    billing_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Total amount charged per billing cycle (COP).',
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING,
    )
    start_date = models.DateField(
        help_text='Date from which the subscription is active and billable.',
    )
    next_billing_date = models.DateField(
        null=True, blank=True,
        help_text='Next date a payment is due.',
    )
    is_archived = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Hidden from subscription lists; row kept for audit.',
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.project.name} — {self.get_plan_display()} (${self.billing_amount:,.0f} COP)'

    @property
    def billing_months(self):
        return self.PLAN_MONTHS.get(self.plan, 1)

    def calculate_amounts(self):
        """Recalculate effective_monthly_amount and billing_amount from base + plan."""
        from decimal import Decimal
        factor = (Decimal(100) - Decimal(self.discount_percent)) / Decimal(100)
        self.effective_monthly_amount = round(self.base_monthly_amount * factor, 2)
        self.billing_amount = round(self.effective_monthly_amount * self.billing_months, 2)


class Payment(models.Model):
    """
    A single payment record for a hosting subscription billing cycle.
    Linked to Wompi transactions for payment processing.
    """

    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'
    STATUS_OVERDUE = 'overdue'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_PROCESSING, 'Procesando'),
        (STATUS_PAID, 'Pagado'),
        (STATUS_FAILED, 'Fallido'),
        (STATUS_OVERDUE, 'Vencido'),
    ]

    subscription = models.ForeignKey(
        HostingSubscription, on_delete=models.PROTECT, related_name='payments',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=300, blank=True, default='')
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    due_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING,
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    wompi_transaction_id = models.CharField(max_length=100, blank=True, default='')
    wompi_payment_link_id = models.CharField(max_length=100, blank=True, default='')
    wompi_payment_link_url = models.URLField(max_length=500, blank=True, default='')
    is_archived = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Hidden from default payment lists; row kept for audit.',
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-billing_period_start']

    def __str__(self):
        return f'Payment ${self.amount:,.0f} — {self.get_status_display()} ({self.billing_period_start} → {self.billing_period_end})'


class PaymentHistory(models.Model):
    """Append-only log of payment status transitions."""

    SOURCE_API = 'api'
    SOURCE_WOMPI_LINK = 'wompi_link'
    SOURCE_WEBHOOK = 'webhook'
    SOURCE_WOMPI_VERIFY = 'wompi_verify'
    SOURCE_SYSTEM = 'system'
    SOURCE_CHOICES = [
        (SOURCE_API, 'API'),
        (SOURCE_WOMPI_LINK, 'Wompi payment link'),
        (SOURCE_WEBHOOK, 'Wompi webhook'),
        (SOURCE_WOMPI_VERIFY, 'Wompi verify'),
        (SOURCE_SYSTEM, 'System'),
    ]

    payment = models.ForeignKey(
        Payment, on_delete=models.PROTECT, related_name='history',
    )
    from_status = models.CharField(max_length=20, choices=Payment.STATUS_CHOICES)
    to_status = models.CharField(max_length=20, choices=Payment.STATUS_CHOICES)
    source = models.CharField(
        max_length=32, choices=SOURCE_CHOICES, blank=True, default='',
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment', '-created_at']),
        ]

    def __str__(self):
        return f'{self.from_status} → {self.to_status} (payment {self.payment_id})'
