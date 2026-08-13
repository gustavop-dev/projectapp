"""Serializers for the panel Projects module (Plataforma space).

Read shape for ``/api/projects/``: the listing row speaks the panel's
language — the client travels as UserProfile id plus display name (the
model's FK points at ``auth.User``), and each row carries the counts of
accounting records hanging off the project.
"""

from rest_framework import serializers

from accounts.models import Project, UserProfile
from accounts.services.proposal_client_service import build_client_display_name

# ``archived`` is never a form choice: a project is archived through its
# dedicated endpoint, and it is not born that way either.
_EDITABLE_STATUS_CHOICES = [
    choice for choice in Project.STATUS_CHOICES
    if choice[0] != Project.STATUS_ARCHIVED
]


class PanelProjectSerializer(serializers.ModelSerializer):
    """Listing row for ``/panel/projects``."""

    status_label = serializers.CharField(source='status_display', read_only=True)
    client = serializers.SerializerMethodField()
    hostings_count = serializers.IntegerField(read_only=True)
    incomes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'status', 'status_label',
            'created_at', 'client', 'hostings_count', 'incomes_count',
        ]
        read_only_fields = fields

    def get_client(self, project):
        profile = getattr(project.client, 'profile', None)
        if profile is None:
            # A client user without a profile row predates the platform
            # onboarding; the panel still needs something to render.
            return {
                'profile_id': None,
                'name': project.client.get_full_name() or project.client.email,
                'company': '',
            }
        return {
            'profile_id': profile.pk,
            'name': build_client_display_name(profile),
            'company': profile.company_name or '',
        }


class CreatePanelProjectSerializer(serializers.Serializer):
    """Create payload: the PA-38 minimum — name and client, the rest optional.

    The client arrives as a UserProfile id (what the panel's autocomplete
    carries) and lands on the model's ``client`` User FK. A same-name project
    for the same client is legal: the duplicate warning lives client-side
    and never blocks.
    """

    name = serializers.CharField(max_length=200)
    client_profile_id = serializers.IntegerField()
    description = serializers.CharField(
        required=False, allow_blank=True, default='',
    )
    status = serializers.ChoiceField(
        choices=_EDITABLE_STATUS_CHOICES,
        required=False,
        default=Project.STATUS_ACTIVE,
    )

    def validate_client_profile_id(self, value):
        profile = UserProfile.objects.clients().filter(pk=value).first()
        if profile is None:
            raise serializers.ValidationError(
                'Ese cliente no existe o no es un perfil de cliente.'
            )
        self.client_profile = profile
        return value

    def create(self, validated_data):
        return Project.objects.create(
            name=validated_data['name'],
            description=validated_data.get('description', ''),
            status=validated_data.get('status', Project.STATUS_ACTIVE),
            client=self.client_profile.user,
        )


class UpdatePanelProjectSerializer(serializers.ModelSerializer):
    """Partial update with the platform's field semantics, panel-scoped.

    Same max lengths and choices as the platform ``UpdateProjectSerializer``,
    restricted to what the panel edits; the client is immutable here and the
    archive transition belongs to its dedicated endpoint.
    """

    status = serializers.ChoiceField(
        choices=_EDITABLE_STATUS_CHOICES, required=False,
    )

    class Meta:
        model = Project
        fields = ['name', 'description', 'status']
