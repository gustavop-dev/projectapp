from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers

from accounts.models import UserProfile

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class VerifyOnboardingSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(min_length=8, write_only=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('La contraseña debe tener al menos 8 caracteres.')
        return value


class ResendCodeSerializer(serializers.Serializer):
    """No fields needed — the user is identified via the verification token."""
    pass


class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    avatar_display_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'user_id', 'email', 'first_name', 'last_name',
            'role', 'company_name', 'phone', 'cedula',
            'date_of_birth', 'gender', 'education_level',
            'avatar_display_url', 'is_onboarded', 'profile_completed',
            'theme_color', 'cover_image', 'custom_cover_image',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'role', 'is_onboarded', 'profile_completed',
            'created_at', 'updated_at',
        ]

    def get_avatar_display_url(self, obj):
        request = self.context.get('request')
        url = obj.avatar_display_url
        if url and request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url


class UpdateProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    company_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    cedula = serializers.CharField(max_length=20, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=UserProfile.GENDER_CHOICES, required=False, allow_blank=True,
    )
    education_level = serializers.ChoiceField(
        choices=UserProfile.EDUCATION_CHOICES, required=False, allow_blank=True,
    )
    avatar = serializers.ImageField(required=False, allow_null=True)
    theme_color = serializers.CharField(max_length=7, required=False, allow_blank=True)
    cover_image = serializers.CharField(max_length=300, required=False, allow_blank=True)
    custom_cover_image = serializers.ImageField(required=False, allow_null=True)


class CompleteProfileSerializer(serializers.Serializer):
    """Mandatory profile completion after first onboarding."""
    company_name = serializers.CharField(max_length=200)
    phone = serializers.CharField(max_length=30)
    cedula = serializers.CharField(max_length=20)
    date_of_birth = serializers.DateField()
    gender = serializers.ChoiceField(choices=UserProfile.GENDER_CHOICES)
    education_level = serializers.ChoiceField(choices=UserProfile.EDUCATION_CHOICES)
    avatar = serializers.ImageField(required=False, allow_null=True)
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)

    def validate_cedula(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('La cédula es obligatoria.')
        return value

    def validate_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('El teléfono es obligatorio.')
        return value


class AdminListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    user_id = serializers.IntegerField(source='user.id')
    is_active = serializers.BooleanField(source='user.is_active')

    class Meta:
        model = UserProfile
        fields = [
            'user_id', 'email', 'first_name', 'last_name',
            'is_onboarded', 'is_active', 'created_at',
        ]


class CreateAdminSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(Q(email=value) | Q(username=value)).exists():
            raise serializers.ValidationError('Ya existe un usuario con este email.')
        return value


class CreateClientSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    company_name = serializers.CharField(max_length=200, required=False, default='')
    phone = serializers.CharField(max_length=30, required=False, default='')

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(Q(email=value) | Q(username=value)).exists():
            raise serializers.ValidationError('Ya existe un usuario con este email.')
        return value


class UpdateClientSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    company_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)


class ClientListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    user_id = serializers.IntegerField(source='user.id')
    is_active = serializers.BooleanField(source='user.is_active')
    avatar_display_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'user_id', 'email', 'first_name', 'last_name',
            'company_name', 'phone', 'is_onboarded', 'is_active',
            'profile_completed', 'avatar_display_url', 'created_at',
        ]

    def get_avatar_display_url(self, obj):
        request = self.context.get('request')
        url = obj.avatar_display_url
        if url and request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url


# =========================================================================
# Project serializers
# =========================================================================

from accounts.models import Project  # noqa: E402


class ProjectListSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    client_email = serializers.EmailField(source='client.email', read_only=True)
    client_id = serializers.IntegerField(source='client.id', read_only=True)
    client_company = serializers.SerializerMethodField()
    proposal_id = serializers.SerializerMethodField()
    proposal_title = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'status', 'progress',
            'start_date', 'estimated_end_date',
            'client_id', 'client_name', 'client_email', 'client_company',
            'proposal_id', 'proposal_title',
            'hosting_start_date',
            'created_at', 'updated_at',
        ]

    def get_proposal_id(self, obj):
        bp = obj.linked_business_proposal()
        return bp.id if bp else None

    def get_proposal_title(self, obj):
        bp = obj.linked_business_proposal()
        return bp.title if bp else None

    def get_client_name(self, obj):
        u = obj.client
        return f'{u.first_name} {u.last_name}'.strip() or u.email

    def get_client_company(self, obj):
        profile = getattr(obj.client, 'profile', None)
        return profile.company_name if profile else ''


class ProjectDetailSerializer(ProjectListSerializer):
    payment_milestones = serializers.SerializerMethodField()
    hosting_tiers = serializers.JSONField(read_only=True)
    has_subscription = serializers.SerializerMethodField()

    class Meta(ProjectListSerializer.Meta):
        fields = ProjectListSerializer.Meta.fields + [
            'payment_milestones', 'hosting_tiers', 'has_subscription',
        ]

    def get_payment_milestones(self, obj):
        """Only visible to admins."""
        request = self.context.get('request')
        profile = getattr(request.user, 'profile', None) if request else None
        if profile and profile.is_admin:
            return obj.payment_milestones or []
        return []

    def get_has_subscription(self, obj):
        return hasattr(obj, 'hosting_subscription')


class CreateProjectSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, default='', allow_blank=True)
    client_id = serializers.IntegerField()
    proposal_id = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=Project.STATUS_CHOICES, default=Project.STATUS_ACTIVE,
    )
    progress = serializers.IntegerField(min_value=0, max_value=100, default=0)
    start_date = serializers.DateField(required=False, allow_null=True)
    estimated_end_date = serializers.DateField(required=False, allow_null=True)
    hosting_start_date = serializers.DateField(required=False, allow_null=True)

    def validate_client_id(self, value):
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('Cliente no encontrado.')
        profile = getattr(user, 'profile', None)
        if not profile or profile.role != UserProfile.ROLE_CLIENT:
            raise serializers.ValidationError('El usuario no es un cliente.')
        return value

    def validate_proposal_id(self, value):
        if value is not None:
            from content.models import BusinessProposal
            bp = BusinessProposal.objects.filter(id=value).select_related('deliverable').first()
            if not bp:
                raise serializers.ValidationError('Propuesta no encontrada.')
            if bp.deliverable_id:
                raise serializers.ValidationError(
                    'Esta propuesta ya está vinculada a un proyecto (entregable).',
                )
        return value


class UpdateProjectSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=Project.STATUS_CHOICES, required=False)
    progress = serializers.IntegerField(min_value=0, max_value=100, required=False)
    start_date = serializers.DateField(required=False, allow_null=True)
    estimated_end_date = serializers.DateField(required=False, allow_null=True)


# =========================================================================
# Requirement serializers
# =========================================================================

from accounts.models import Requirement, RequirementComment, RequirementHistory  # noqa: E402


class RequirementCommentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = RequirementComment
        fields = ['id', 'content', 'is_internal', 'user_email', 'user_name', 'created_at']

    def get_user_name(self, obj):
        u = obj.user
        return f'{u.first_name} {u.last_name}'.strip() or u.email


class RequirementHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(source='changed_by.email', read_only=True, default='')

    class Meta:
        model = RequirementHistory
        fields = ['id', 'from_status', 'to_status', 'changed_by_email', 'created_at']


class RequirementListSerializer(serializers.ModelSerializer):
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Requirement
        fields = [
            'id', 'deliverable_id', 'title', 'description', 'configuration', 'flow',
            'status', 'priority', 'order',
            'source_epic_key', 'source_epic_title', 'source_flow_key', 'synced_from_proposal',
            'is_archived', 'archived_at',
            'comments_count', 'created_at', 'updated_at',
        ]

    def get_comments_count(self, obj):
        return getattr(obj, '_comments_count', obj.comments.count())


class RequirementDetailSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()
    history = RequirementHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Requirement
        fields = [
            'id', 'deliverable_id', 'title', 'description', 'configuration', 'flow',
            'status', 'priority', 'order',
            'source_epic_key', 'source_epic_title', 'source_flow_key', 'synced_from_proposal',
            'is_archived', 'archived_at',
            'comments', 'history',
            'created_at', 'updated_at',
        ]

    def get_comments(self, obj):
        request = self.context.get('request')
        profile = getattr(request.user, 'profile', None) if request else None
        qs = obj.comments.select_related('user').all()
        if not profile or not profile.is_admin:
            qs = qs.filter(is_internal=False)
        return RequirementCommentSerializer(qs, many=True).data


class CreateRequirementSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=300)
    description = serializers.CharField(required=False, default='', allow_blank=True)
    configuration = serializers.CharField(required=False, default='', allow_blank=True)
    flow = serializers.CharField(required=False, default='', allow_blank=True)
    deliverable_id = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=Requirement.STATUS_CHOICES, default=Requirement.STATUS_BACKLOG,
    )
    priority = serializers.ChoiceField(
        choices=Requirement.PRIORITY_CHOICES, default=Requirement.PRIORITY_MEDIUM,
    )


class UpdateRequirementSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=300, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    configuration = serializers.CharField(required=False, allow_blank=True)
    flow = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=Requirement.STATUS_CHOICES, required=False)
    priority = serializers.ChoiceField(choices=Requirement.PRIORITY_CHOICES, required=False)
    order = serializers.IntegerField(min_value=0, required=False)
    is_archived = serializers.BooleanField(required=False)


class MoveRequirementSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Requirement.STATUS_CHOICES)
    order = serializers.IntegerField(min_value=0, default=0)


class CreateCommentSerializer(serializers.Serializer):
    content = serializers.CharField()
    is_internal = serializers.BooleanField(default=False)


# =========================================================================
# Change Request serializers
# =========================================================================

from accounts.models import ChangeRequest, ChangeRequestComment  # noqa: E402


class ChangeRequestCommentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = ChangeRequestComment
        fields = ['id', 'content', 'is_internal', 'user_email', 'user_name', 'created_at']

    def get_user_name(self, obj):
        u = obj.user
        return f'{u.first_name} {u.last_name}'.strip() or u.email


class ChangeRequestListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    comments_count = serializers.SerializerMethodField()
    screenshot_url = serializers.SerializerMethodField()

    class Meta:
        model = ChangeRequest
        fields = [
            'id', 'title', 'description', 'module_or_screen',
            'suggested_priority', 'is_urgent', 'status',
            'admin_response', 'estimated_cost', 'estimated_time',
            'linked_requirement_id', 'screenshot_url',
            'is_archived', 'archived_at',
            'created_by_name', 'created_by_email',
            'comments_count', 'created_at', 'updated_at',
        ]

    def get_created_by_name(self, obj):
        u = obj.created_by
        return f'{u.first_name} {u.last_name}'.strip() or u.email

    def get_comments_count(self, obj):
        return getattr(obj, '_comments_count', obj.comments.count())

    def get_screenshot_url(self, obj):
        if not obj.screenshot:
            return None
        request = self.context.get('request')
        url = obj.screenshot.url
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url


class ChangeRequestDetailSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    comments = serializers.SerializerMethodField()
    screenshot_url = serializers.SerializerMethodField()

    class Meta:
        model = ChangeRequest
        fields = [
            'id', 'title', 'description', 'module_or_screen',
            'suggested_priority', 'is_urgent', 'status',
            'admin_response', 'estimated_cost', 'estimated_time',
            'linked_requirement_id', 'screenshot_url',
            'is_archived', 'archived_at',
            'created_by_name', 'created_by_email',
            'comments', 'created_at', 'updated_at',
        ]

    def get_created_by_name(self, obj):
        u = obj.created_by
        return f'{u.first_name} {u.last_name}'.strip() or u.email

    def get_comments(self, obj):
        request = self.context.get('request')
        profile = getattr(request.user, 'profile', None) if request else None
        qs = obj.comments.select_related('user').all()
        if not profile or not profile.is_admin:
            qs = qs.filter(is_internal=False)
        return ChangeRequestCommentSerializer(qs, many=True).data

    def get_screenshot_url(self, obj):
        if not obj.screenshot:
            return None
        request = self.context.get('request')
        url = obj.screenshot.url
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url


class CreateChangeRequestSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=300)
    description = serializers.CharField(required=False, default='', allow_blank=True)
    module_or_screen = serializers.CharField(max_length=200, required=False, default='', allow_blank=True)
    suggested_priority = serializers.ChoiceField(
        choices=ChangeRequest.PRIORITY_CHOICES, default=ChangeRequest.PRIORITY_MEDIUM,
    )
    is_urgent = serializers.BooleanField(default=False)
    screenshot = serializers.ImageField(required=False, allow_null=True)


class EvaluateChangeRequestSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ChangeRequest.STATUS_CHOICES)
    admin_response = serializers.CharField(required=False, default='', allow_blank=True)
    estimated_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True,
    )
    estimated_time = serializers.CharField(max_length=100, required=False, default='', allow_blank=True)


class CreateChangeRequestCommentSerializer(serializers.Serializer):
    content = serializers.CharField()
    is_internal = serializers.BooleanField(default=False)


# =========================================================================
# Bug Report serializers
# =========================================================================

from accounts.models import BugComment, BugReport, Deliverable  # noqa: E402


class BugCommentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = BugComment
        fields = ['id', 'content', 'is_internal', 'user_email', 'user_name', 'created_at']

    def get_user_name(self, obj):
        u = obj.user
        return f'{u.first_name} {u.last_name}'.strip() or u.email


class BugReportListSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.SerializerMethodField()
    reported_by_email = serializers.EmailField(source='reported_by.email', read_only=True)
    comments_count = serializers.SerializerMethodField()
    screenshot_url = serializers.SerializerMethodField()
    deliverable_id = serializers.IntegerField(source='deliverable.id', read_only=True)
    deliverable_title = serializers.CharField(source='deliverable.title', read_only=True)

    class Meta:
        model = BugReport
        fields = [
            'id', 'deliverable_id', 'deliverable_title',
            'title', 'description', 'severity', 'status',
            'environment', 'device_browser', 'is_recurring',
            'steps_to_reproduce', 'expected_behavior', 'actual_behavior',
            'admin_response', 'linked_bug_id', 'screenshot_url',
            'is_archived', 'archived_at',
            'reported_by_name', 'reported_by_email',
            'comments_count', 'created_at', 'updated_at',
        ]

    def get_reported_by_name(self, obj):
        u = obj.reported_by
        return f'{u.first_name} {u.last_name}'.strip() or u.email

    def get_comments_count(self, obj):
        return getattr(obj, '_comments_count', obj.comments.count())

    def get_screenshot_url(self, obj):
        if not obj.screenshot:
            return None
        request = self.context.get('request')
        url = obj.screenshot.url
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url


class BugReportDetailSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.SerializerMethodField()
    reported_by_email = serializers.EmailField(source='reported_by.email', read_only=True)
    comments = serializers.SerializerMethodField()
    screenshot_url = serializers.SerializerMethodField()
    deliverable_id = serializers.IntegerField(source='deliverable.id', read_only=True)
    deliverable_title = serializers.CharField(source='deliverable.title', read_only=True)

    class Meta:
        model = BugReport
        fields = [
            'id', 'deliverable_id', 'deliverable_title',
            'title', 'description', 'severity', 'status',
            'environment', 'device_browser', 'is_recurring',
            'steps_to_reproduce', 'expected_behavior', 'actual_behavior',
            'admin_response', 'linked_bug_id', 'screenshot_url',
            'is_archived', 'archived_at',
            'reported_by_name', 'reported_by_email',
            'comments', 'created_at', 'updated_at',
        ]

    def get_reported_by_name(self, obj):
        u = obj.reported_by
        return f'{u.first_name} {u.last_name}'.strip() or u.email

    def get_comments(self, obj):
        request = self.context.get('request')
        profile = getattr(request.user, 'profile', None) if request else None
        qs = obj.comments.select_related('user').all()
        if not profile or not profile.is_admin:
            qs = qs.filter(is_internal=False)
        return BugCommentSerializer(qs, many=True).data

    def get_screenshot_url(self, obj):
        if not obj.screenshot:
            return None
        request = self.context.get('request')
        url = obj.screenshot.url
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url


class CreateBugReportSerializer(serializers.Serializer):
    deliverable_id = serializers.IntegerField()
    title = serializers.CharField(max_length=300)
    description = serializers.CharField(required=False, default='', allow_blank=True)
    severity = serializers.ChoiceField(
        choices=BugReport.SEVERITY_CHOICES, default=BugReport.SEVERITY_MEDIUM,
    )
    steps_to_reproduce = serializers.ListField(
        child=serializers.CharField(), required=False, default=list,
    )
    expected_behavior = serializers.CharField(required=False, default='', allow_blank=True)
    actual_behavior = serializers.CharField(required=False, default='', allow_blank=True)
    environment = serializers.ChoiceField(
        choices=BugReport.ENV_CHOICES, default=BugReport.ENV_PRODUCTION,
    )
    device_browser = serializers.CharField(max_length=200, required=False, default='', allow_blank=True)
    is_recurring = serializers.BooleanField(default=False)
    screenshot = serializers.ImageField(required=False, allow_null=True)

    def validate_deliverable_id(self, value):
        project = self.context.get('project')
        if project is None:
            raise serializers.ValidationError('Contexto de proyecto requerido.')
        if not Deliverable.objects.filter(pk=value, project=project, is_archived=False).exists():
            raise serializers.ValidationError(
                'Entregable no encontrado, archivado o no pertenece a este proyecto.',
            )
        return value


class EvaluateBugReportSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=BugReport.STATUS_CHOICES)
    admin_response = serializers.CharField(required=False, default='', allow_blank=True)
    linked_bug_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        linked_id = attrs.get('linked_bug_id')
        bug = self.context.get('bug')
        if linked_id is not None and bug is not None:
            other = BugReport.objects.filter(pk=linked_id).first()
            if not other:
                raise serializers.ValidationError({'linked_bug_id': 'Bug vinculado no encontrado.'})
            if other.is_archived:
                raise serializers.ValidationError({'linked_bug_id': 'El bug vinculado está archivado.'})
            if other.deliverable_id != bug.deliverable_id:
                raise serializers.ValidationError({
                    'linked_bug_id': 'El bug vinculado debe pertenecer al mismo entregable.',
                })
        return attrs


class CreateBugCommentSerializer(serializers.Serializer):
    content = serializers.CharField()
    is_internal = serializers.BooleanField(default=False)


# =========================================================================
# Deliverable serializers
# =========================================================================

from accounts.models import (  # noqa: E402
    DeliverableClientFolder,
    DeliverableClientUpload,
    DeliverableFile,
    DeliverableVersion,
)


class DeliverableVersionSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    file_name = serializers.CharField(read_only=True)
    file_size = serializers.IntegerField(read_only=True)

    class Meta:
        model = DeliverableVersion
        fields = [
            'id', 'version_number', 'file_url', 'file_name', 'file_size',
            'uploaded_by_name', 'created_at',
        ]

    def get_uploaded_by_name(self, obj):
        u = obj.uploaded_by
        return f'{u.first_name} {u.last_name}'.strip() or u.email

    def get_file_url(self, obj):
        if not obj.file:
            return None
        request = self.context.get('request')
        url = obj.file.url
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url


class DeliverableListSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    file_name = serializers.CharField(read_only=True)
    file_size = serializers.IntegerField(read_only=True)
    versions_count = serializers.SerializerMethodField()

    class Meta:
        model = Deliverable
        fields = [
            'id', 'title', 'description', 'category', 'current_version',
            'file_url', 'file_name', 'file_size',
            'uploaded_by_name', 'versions_count',
            'source_epic_key', 'source_epic_title',
            'is_archived', 'archived_at',
            'created_at', 'updated_at',
        ]

    def get_uploaded_by_name(self, obj):
        u = obj.uploaded_by
        return f'{u.first_name} {u.last_name}'.strip() or u.email

    def get_file_url(self, obj):
        if not obj.file:
            return None
        request = self.context.get('request')
        url = obj.file.url
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url

    def get_versions_count(self, obj):
        return getattr(obj, '_versions_count', obj.versions.count())


class DeliverableFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DeliverableFile
        fields = ['id', 'title', 'category', 'file_url', 'uploaded_by_name', 'created_at']

    def get_file_url(self, obj):
        if not obj.file:
            return None
        request = self.context.get('request')
        url = obj.file.url
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url

    def get_uploaded_by_name(self, obj):
        u = obj.uploaded_by
        return f'{u.first_name} {u.last_name}'.strip() or u.email


class DeliverableClientFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliverableClientFolder
        fields = ['id', 'name', 'order', 'created_at']


class DeliverableClientUploadSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = DeliverableClientUpload
        fields = [
            'id', 'folder', 'title', 'file_url', 'file_name',
            'uploaded_by_name', 'created_at',
        ]

    def get_file_url(self, obj):
        if not obj.file:
            return None
        request = self.context.get('request')
        url = obj.file.url
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url

    def get_uploaded_by_name(self, obj):
        u = obj.uploaded_by
        return f'{u.first_name} {u.last_name}'.strip() or u.email


class CreateDeliverableClientFolderSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    order = serializers.IntegerField(required=False, default=0, min_value=0)


class CreateDeliverableClientUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(required=False, default='', allow_blank=True)
    folder_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_file(self, f):
        max_bytes = 15 * 1024 * 1024
        if f.size > max_bytes:
            raise serializers.ValidationError('El PDF no puede superar 15 MB.')
        name = (getattr(f, 'name', '') or '').lower()
        if not name.endswith('.pdf'):
            raise serializers.ValidationError('Solo se permiten archivos PDF.')
        ct = (getattr(f, 'content_type', '') or '').lower()
        if ct and 'pdf' not in ct:
            raise serializers.ValidationError('El archivo debe ser PDF.')
        return f

    def validate(self, attrs):
        deliverable = self.context.get('deliverable')
        fid = attrs.get('folder_id')
        if fid is not None and deliverable is not None:
            if not DeliverableClientFolder.objects.filter(pk=fid, deliverable=deliverable).exists():
                raise serializers.ValidationError(
                    {'folder_id': 'La carpeta no pertenece a este entregable.'},
                )
        return attrs


class DeliverableDetailSerializer(DeliverableListSerializer):
    versions = serializers.SerializerMethodField()
    has_business_proposal = serializers.SerializerMethodField()
    proposal_id = serializers.SerializerMethodField()
    proposal_title = serializers.SerializerMethodField()
    attachment_files = serializers.SerializerMethodField()
    pdf_download_paths = serializers.SerializerMethodField()
    client_folders = serializers.SerializerMethodField()
    client_uploads = serializers.SerializerMethodField()
    collection_accounts = serializers.SerializerMethodField()

    class Meta(DeliverableListSerializer.Meta):
        fields = DeliverableListSerializer.Meta.fields + [
            'versions',
            'has_business_proposal',
            'proposal_id',
            'proposal_title',
            'attachment_files',
            'pdf_download_paths',
            'source_epic_key',
            'source_epic_title',
            'client_folders',
            'client_uploads',
            'collection_accounts',
        ]

    def get_versions(self, obj):
        qs = obj.versions.select_related('uploaded_by').all()
        return DeliverableVersionSerializer(qs, many=True, context=self.context).data

    def get_has_business_proposal(self, obj):
        bp = getattr(obj, 'business_proposal', None)
        return bp is not None

    def get_proposal_id(self, obj):
        bp = getattr(obj, 'business_proposal', None)
        return bp.id if bp else None

    def get_proposal_title(self, obj):
        bp = getattr(obj, 'business_proposal', None)
        return bp.title if bp else None

    def get_attachment_files(self, obj):
        qs = obj.attachment_files.select_related('uploaded_by').all()
        return DeliverableFileSerializer(qs, many=True, context=self.context).data

    def get_pdf_download_paths(self, obj):
        pid = obj.project_id
        did = obj.id
        return {
            'commercial': f'projects/{pid}/deliverables/{did}/download/commercial-proposal-pdf/',
            'technical': f'projects/{pid}/deliverables/{did}/download/technical-document-pdf/',
        }

    def get_client_folders(self, obj):
        qs = obj.client_folders.all()
        return DeliverableClientFolderSerializer(qs, many=True).data

    def get_client_uploads(self, obj):
        qs = obj.client_uploads.select_related('uploaded_by', 'folder').all()
        return DeliverableClientUploadSerializer(qs, many=True, context=self.context).data

    def get_collection_accounts(self, obj):
        try:
            from content.models import Document
            from content.services.document_type_codes import COLLECTION_ACCOUNT
        except ImportError:
            return []

        qs = Document.objects.filter(
            project_id=obj.project_id,
            document_type__code=COLLECTION_ACCOUNT,
            deliverable_id=obj.id,
        ).select_related('document_type').order_by('-created_at')[:50]
        return [
            {
                'id': d.id,
                'uuid': str(d.uuid),
                'title': d.title,
                'public_number': d.public_number,
                'commercial_status': d.commercial_status,
            }
            for d in qs
        ]


class CreateDeliverableSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=300)
    description = serializers.CharField(required=False, default='', allow_blank=True)
    category = serializers.ChoiceField(
        choices=Deliverable.CATEGORY_CHOICES, default=Deliverable.CATEGORY_OTHER,
    )
    file = serializers.FileField()


class UpdateDeliverableSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=300, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    category = serializers.ChoiceField(choices=Deliverable.CATEGORY_CHOICES, required=False)
    is_archived = serializers.BooleanField(required=False)


class UploadNewVersionSerializer(serializers.Serializer):
    file = serializers.FileField()


class CreateDeliverableFileSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(required=False, default='', allow_blank=True)
    category = serializers.ChoiceField(
        choices=Deliverable.CATEGORY_CHOICES, default=Deliverable.CATEGORY_OTHER,
    )


# =========================================================================
# Notification serializers
# =========================================================================

from accounts.models import Notification  # noqa: E402


class NotificationSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField()
    deliverable_title = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message',
            'related_object_type', 'related_object_id',
            'project', 'project_name',
            'deliverable', 'deliverable_title',
            'is_read', 'created_at',
        ]

    def get_project_name(self, obj):
        if obj.project:
            return obj.project.name
        return None

    def get_deliverable_title(self, obj):
        if obj.deliverable:
            return obj.deliverable.title
        return None


# =========================================================================
# Payment / Subscription serializers
# =========================================================================

from accounts.models import HostingSubscription, Payment, PaymentHistory  # noqa: E402


class PaymentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentHistory
        fields = ['id', 'from_status', 'to_status', 'source', 'metadata', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(source='subscription.project_id', read_only=True)
    project_name = serializers.SerializerMethodField()
    history = PaymentHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'amount', 'description',
            'billing_period_start', 'billing_period_end', 'due_date',
            'status', 'paid_at',
            'wompi_payment_link_url',
            'is_archived', 'archived_at',
            'project_id', 'project_name',
            'history',
            'created_at',
        ]

    def get_project_name(self, obj):
        return obj.subscription.project.name


class HostingSubscriptionSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField()
    project_id = serializers.IntegerField(source='project.id', read_only=True)
    plan_display = serializers.CharField(source='get_plan_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = HostingSubscription
        fields = [
            'id', 'plan', 'plan_display',
            'base_monthly_amount', 'discount_percent',
            'effective_monthly_amount', 'billing_amount',
            'status', 'status_display',
            'start_date', 'next_billing_date',
            'is_archived', 'archived_at',
            'project_id', 'project_name',
            'payments', 'created_at', 'updated_at',
        ]

    def get_project_name(self, obj):
        return obj.project.name


class HostingSubscriptionListSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField()
    project_id = serializers.IntegerField(source='project.id', read_only=True)
    plan_display = serializers.CharField(source='get_plan_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    pending_payments = serializers.SerializerMethodField()

    class Meta:
        model = HostingSubscription
        fields = [
            'id', 'plan', 'plan_display',
            'base_monthly_amount', 'discount_percent',
            'effective_monthly_amount', 'billing_amount',
            'status', 'status_display',
            'start_date', 'next_billing_date',
            'is_archived', 'archived_at',
            'project_id', 'project_name',
            'pending_payments', 'created_at',
        ]

    def get_project_name(self, obj):
        return obj.project.name

    def get_pending_payments(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now().date() + timedelta(days=7)
        return obj.payments.filter(
            is_archived=False,
            status__in=['pending', 'overdue', 'failed'],
            due_date__lte=cutoff,
        ).count()


class UpdateSubscriptionSerializer(serializers.Serializer):
    plan = serializers.ChoiceField(
        choices=HostingSubscription.PLAN_CHOICES, required=False,
    )
    status = serializers.ChoiceField(
        choices=HostingSubscription.STATUS_CHOICES, required=False,
    )
    is_archived = serializers.BooleanField(required=False)


class ProposalSummarySerializer(serializers.Serializer):
    """Lightweight serializer for proposal selection in project creation."""
    id = serializers.IntegerField()
    title = serializers.CharField()
    client_name = serializers.CharField()
    client_email = serializers.EmailField()
    total_investment = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    hosting_percent = serializers.IntegerField()
    hosting_discount_semiannual = serializers.IntegerField()
    hosting_discount_quarterly = serializers.IntegerField()
    status = serializers.CharField()
