"""
Serializers for the proposal admin panel's client management surface.

These wrap ``accounts.UserProfile`` (filtered to ``role='client'``) with the
shape expected by ``/panel/clients`` and the proposal create/edit autocomplete.
"""

from rest_framework import serializers

from accounts.models import UserProfile
from accounts.services.proposal_client_service import build_client_display_name


class ProposalClientSerializer(serializers.ModelSerializer):
    """
    Full serializer for the proposal-side client (UserProfile + nested User).

    Read fields:
        - ``name``: derived from User.first_name + last_name, falling back to
          company_name or email.
        - ``email``: User.email (may be a placeholder ``cliente_<id>@temp.example.com``).
        - ``phone``: UserProfile.phone.
        - ``company``: UserProfile.company_name.
        - ``is_email_placeholder`` / ``is_onboarded``: status flags.
        - ``total_proposals`` / ``is_orphan``: read from queryset annotations
          when available, falling back to per-instance queries otherwise.

    Write fields (POST/PATCH):
        - ``name``, ``email``, ``phone``, ``company`` are accepted but the
          underlying writes are routed through ``proposal_client_service``
          (the views call ``get_or_create_client_for_proposal`` /
          ``update_client_profile`` instead of using ``serializer.save``).
    """

    name = serializers.CharField(required=False, allow_blank=True, max_length=311)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=30)
    company = serializers.CharField(
        source='company_name',
        required=False,
        allow_blank=True,
        max_length=200,
    )
    is_email_placeholder = serializers.BooleanField(read_only=True)
    total_proposals = serializers.SerializerMethodField()
    is_orphan = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'name',
            'email',
            'phone',
            'company',
            'is_onboarded',
            'is_email_placeholder',
            'total_proposals',
            'is_orphan',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'is_onboarded',
            'is_email_placeholder',
            'total_proposals',
            'is_orphan',
            'created_at',
            'updated_at',
        )

    def validate_email(self, value):
        # Lazy import avoids a circular dependency with content.serializers.proposal,
        # which imports ProposalClientSerializer at module load time.
        from content.serializers.proposal import _validate_client_email_mx

        return _validate_client_email_mx(value)

    def get_total_proposals(self, obj):
        # Annotated alias `proposals_count` is preferred when the queryset
        # was annotated; fall back to a per-instance query otherwise.
        annotated = getattr(obj, 'proposals_count', None)
        if annotated is not None:
            return annotated
        return obj.proposals.count()

    def get_is_orphan(self, obj):
        if self.get_total_proposals(obj) > 0:
            return False
        projects_annotated = getattr(obj, 'projects_count', None)
        if projects_annotated is not None:
            return projects_annotated == 0
        return not obj.user.projects.exists()

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['name'] = build_client_display_name(instance)
        rep['email'] = instance.user.email or ''
        return rep


class ProposalClientSearchSerializer(serializers.ModelSerializer):
    """Lightweight payload for the autocomplete dropdown (max 20 results)."""

    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    company = serializers.CharField(source='company_name')
    is_email_placeholder = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserProfile
        fields = ('id', 'name', 'email', 'phone', 'company', 'is_email_placeholder')

    def get_name(self, obj):
        return build_client_display_name(obj)

    def get_email(self, obj):
        return obj.user.email or ''
