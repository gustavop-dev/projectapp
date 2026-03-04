from rest_framework import serializers

from content.models import (
    BusinessProposal,
    ProposalSection,
    ProposalRequirementGroup,
    ProposalRequirementItem,
)


class ProposalRequirementItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the ProposalRequirementItem model.
    """

    class Meta:
        model = ProposalRequirementItem
        fields = '__all__'


class ProposalRequirementGroupSerializer(serializers.ModelSerializer):
    """
    Serializer for the ProposalRequirementGroup model, including nested items.
    """
    items = ProposalRequirementItemSerializer(many=True, read_only=True)

    class Meta:
        model = ProposalRequirementGroup
        fields = ('id', 'group_id', 'title', 'description', 'order', 'items')


class ProposalSectionListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing proposal sections in admin views.
    """

    class Meta:
        model = ProposalSection
        fields = ('id', 'section_type', 'title', 'order', 'is_enabled', 'is_wide_panel')


class ProposalSectionDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for proposal sections, including content_json.
    """

    class Meta:
        model = ProposalSection
        fields = '__all__'


class ProposalListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing proposals in admin views.
    Includes computed fields for expiration status.
    """
    days_remaining = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = BusinessProposal
        fields = (
            'id', 'uuid', 'title', 'client_name', 'status',
            'total_investment', 'currency', 'expires_at',
            'view_count', 'created_at', 'days_remaining', 'is_expired',
        )

    def get_days_remaining(self, obj):
        return obj.days_remaining

    def get_is_expired(self, obj):
        return obj.is_expired


class ProposalDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for a business proposal, used by both client and admin detail views.

    Includes nested sections (filtered by is_enabled for client, all for admin),
    nested requirement groups with items, and computed properties.
    """
    sections = serializers.SerializerMethodField()
    requirement_groups = ProposalRequirementGroupSerializer(many=True, read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    public_url = serializers.SerializerMethodField()

    class Meta:
        model = BusinessProposal
        fields = (
            'id', 'uuid', 'title', 'client_name', 'client_email', 'slug',
            'total_investment', 'currency', 'status', 'expires_at',
            'reminder_days', 'reminder_sent_at', 'view_count',
            'first_viewed_at', 'sent_at', 'created_at', 'updated_at',
            'sections', 'requirement_groups',
            'days_remaining', 'is_expired', 'public_url',
        )

    def get_sections(self, obj):
        """
        Return sections ordered by 'order'.
        For public (client) requests, only enabled sections are returned.
        For admin requests, all sections are returned.
        """
        is_admin = self.context.get('is_admin', False)
        qs = obj.sections.all().order_by('order')
        if not is_admin:
            qs = qs.filter(is_enabled=True)
        return ProposalSectionDetailSerializer(qs, many=True).data

    def get_days_remaining(self, obj):
        return obj.days_remaining

    def get_is_expired(self, obj):
        return obj.is_expired

    def get_public_url(self, obj):
        return obj.public_url


class ProposalCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating business proposal metadata.
    """

    class Meta:
        model = BusinessProposal
        fields = (
            'title', 'client_name', 'client_email', 'slug',
            'total_investment', 'currency', 'status',
            'expires_at', 'reminder_days', 'discount_percent',
        )

    def validate_expires_at(self, value):
        """Ensure expiration date is in the future when provided."""
        if value is not None:
            from django.utils import timezone
            if value < timezone.now():
                raise serializers.ValidationError(
                    'Expiration date must be in the future.'
                )
        return value

    def validate(self, attrs):
        """Ensure client_email is set when status is SENT."""
        status = attrs.get('status', getattr(self.instance, 'status', None))
        client_email = attrs.get(
            'client_email',
            getattr(self.instance, 'client_email', ''),
        )
        if status == BusinessProposal.Status.SENT and not client_email:
            raise serializers.ValidationError({
                'client_email': 'Client email is required when sending a proposal.',
            })
        return attrs


class ProposalSectionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a proposal section's content and metadata.
    """

    class Meta:
        model = ProposalSection
        fields = ('title', 'order', 'is_enabled', 'is_wide_panel', 'content_json')

    def validate_content_json(self, value):
        """Ensure content_json is a dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                'content_json must be a JSON object (dict).'
            )
        return value
