from django.contrib.auth import get_user_model
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


class CreateClientSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    company_name = serializers.CharField(max_length=200, required=False, default='')
    phone = serializers.CharField(max_length=30, required=False, default='')

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
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

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'status', 'progress',
            'start_date', 'estimated_end_date',
            'client_id', 'client_name', 'client_email', 'client_company',
            'created_at', 'updated_at',
        ]

    def get_client_name(self, obj):
        u = obj.client
        return f'{u.first_name} {u.last_name}'.strip() or u.email

    def get_client_company(self, obj):
        profile = getattr(obj.client, 'profile', None)
        return profile.company_name if profile else ''


class ProjectDetailSerializer(ProjectListSerializer):
    class Meta(ProjectListSerializer.Meta):
        fields = ProjectListSerializer.Meta.fields


class CreateProjectSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, default='', allow_blank=True)
    client_id = serializers.IntegerField()
    status = serializers.ChoiceField(
        choices=Project.STATUS_CHOICES, default=Project.STATUS_ACTIVE,
    )
    progress = serializers.IntegerField(min_value=0, max_value=100, default=0)
    start_date = serializers.DateField(required=False, allow_null=True)
    estimated_end_date = serializers.DateField(required=False, allow_null=True)

    def validate_client_id(self, value):
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('Cliente no encontrado.')
        profile = getattr(user, 'profile', None)
        if not profile or profile.role != UserProfile.ROLE_CLIENT:
            raise serializers.ValidationError('El usuario no es un cliente.')
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
            'id', 'title', 'description', 'status', 'priority',
            'estimated_hours', 'module', 'order',
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
            'id', 'title', 'description', 'status', 'priority',
            'estimated_hours', 'module', 'order',
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
    status = serializers.ChoiceField(
        choices=Requirement.STATUS_CHOICES, default=Requirement.STATUS_BACKLOG,
    )
    priority = serializers.ChoiceField(
        choices=Requirement.PRIORITY_CHOICES, default=Requirement.PRIORITY_MEDIUM,
    )
    estimated_hours = serializers.DecimalField(
        max_digits=6, decimal_places=1, required=False, allow_null=True,
    )
    module = serializers.CharField(max_length=100, required=False, default='', allow_blank=True)


class UpdateRequirementSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=300, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=Requirement.STATUS_CHOICES, required=False)
    priority = serializers.ChoiceField(choices=Requirement.PRIORITY_CHOICES, required=False)
    estimated_hours = serializers.DecimalField(
        max_digits=6, decimal_places=1, required=False, allow_null=True,
    )
    module = serializers.CharField(max_length=100, required=False, allow_blank=True)
    order = serializers.IntegerField(min_value=0, required=False)


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
