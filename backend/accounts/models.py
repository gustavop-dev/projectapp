import secrets
import string

from django.conf import settings
from django.db import models
from django.utils import timezone

from accounts.services.image_utils import optimize_avatar, optimize_image


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.name} — {self.client.email}'

    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


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

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='requirements',
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_BACKLOG,
    )
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM,
    )
    estimated_hours = models.DecimalField(
        max_digits=6, decimal_places=1, null=True, blank=True,
    )
    module = models.CharField(max_length=100, blank=True, default='')
    order = models.PositiveIntegerField(
        default=0, help_text='Sort order within the column.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return f'{self.title} [{self.get_status_display()}]'


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
    A bug report filed by a client (or admin) for a project.
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

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='bug_reports',
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
    """

    CATEGORY_DESIGNS = 'designs'
    CATEGORY_CREDENTIALS = 'credentials'
    CATEGORY_DOCUMENTS = 'documents'
    CATEGORY_APKS = 'apks'
    CATEGORY_OTHER = 'other'
    CATEGORY_CHOICES = [
        (CATEGORY_DESIGNS, 'Diseños'),
        (CATEGORY_CREDENTIALS, 'Credenciales'),
        (CATEGORY_DOCUMENTS, 'Documentos'),
        (CATEGORY_APKS, 'APKs / Builds'),
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
    file = models.FileField(upload_to='deliverables/')
    current_version = models.PositiveIntegerField(default=1)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='uploaded_deliverables',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', '-updated_at']

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
