"""Serializers for the panel Projects module (Plataforma space).

Read shape for ``/api/projects/``: the listing row speaks the panel's
language — the client travels as UserProfile id plus display name (the
model's FK points at ``auth.User``), and each row carries the counts of
accounting records hanging off the project.
"""

from rest_framework import serializers

from accounts.models import Project
from accounts.services.proposal_client_service import build_client_display_name


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
