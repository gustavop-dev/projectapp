from rest_framework import serializers

from content.models import (
    BusinessProposal,
    EmailTemplateConfig,
    ProposalAlert,
    ProposalSection,
    ProposalRequirementGroup,
    ProposalRequirementItem,
    ProposalShareLink,
    ProposalDefaultConfig,
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
            'id', 'uuid', 'title', 'client_name', 'client_email', 'status',
            'total_investment', 'currency', 'expires_at',
            'view_count', 'created_at', 'days_remaining', 'is_expired',
            'is_active', 'automations_paused', 'responded_at', 'last_activity_at',
            'project_type', 'market_type', 'client_phone',
            'project_type_custom', 'market_type_custom',
            'cached_heat_score', 'engagement_declining',
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
    discounted_investment = serializers.SerializerMethodField()

    change_logs = serializers.SerializerMethodField()

    class Meta:
        model = BusinessProposal
        fields = (
            'id', 'uuid', 'title', 'client_name', 'client_email', 'slug',
            'language', 'total_investment', 'currency', 'hosting_percent',
            'hosting_discount_semiannual', 'hosting_discount_quarterly',
            'status', 'expires_at',
            'reminder_days', 'urgency_reminder_days', 'discount_percent',
            'is_active', 'automations_paused',
            'reminder_sent_at', 'urgency_email_sent_at',
            'project_type', 'market_type', 'client_phone',
            'project_type_custom', 'market_type_custom',
            'last_activity_at',
            'view_count', 'first_viewed_at', 'sent_at', 'responded_at',
            'created_at', 'updated_at',
            'sections', 'requirement_groups', 'change_logs',
            'days_remaining', 'is_expired', 'public_url',
            'discounted_investment', 'selected_modules',
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

    def get_change_logs(self, obj):
        """Return change logs only for admin requests."""
        is_admin = self.context.get('is_admin', False)
        if not is_admin:
            return []
        logs = obj.change_logs.all().order_by('-created_at')[:50]
        return [
            {
                'id': log.id,
                'change_type': log.change_type,
                'description': log.description,
                'created_at': log.created_at.isoformat(),
            }
            for log in logs
        ]

    def get_discounted_investment(self, obj):
        """Return discounted price when discount_percent > 0."""
        if not obj.discount_percent or obj.discount_percent <= 0:
            return None
        from decimal import Decimal
        factor = (Decimal(100) - Decimal(obj.discount_percent)) / Decimal(100)
        return str(round(obj.total_investment * factor, 2))


class ProposalCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating business proposal metadata.
    """

    class Meta:
        model = BusinessProposal
        fields = (
            'title', 'client_name', 'client_email', 'slug',
            'language', 'total_investment', 'currency', 'hosting_percent',
            'hosting_discount_semiannual', 'hosting_discount_quarterly',
            'status', 'expires_at', 'reminder_days', 'urgency_reminder_days',
            'discount_percent', 'is_active', 'automations_paused',
            'project_type', 'market_type', 'client_phone',
            'project_type_custom', 'market_type_custom',
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


# ---------------------------------------------------------------------------
# JSON key → section_type mapping
# ---------------------------------------------------------------------------
SECTION_KEY_MAP = {
    'general': 'greeting',
    'executiveSummary': 'executive_summary',
    'contextDiagnostic': 'context_diagnostic',
    'conversionStrategy': 'conversion_strategy',
    'designUX': 'design_ux',
    'creativeSupport': 'creative_support',
    'developmentStages': 'development_stages',
    'processMethodology': 'process_methodology',
    'functionalRequirements': 'functional_requirements',
    'timeline': 'timeline',
    'investment': 'investment',
    'proposalSummary': 'proposal_summary',
    'finalNote': 'final_note',
    'nextSteps': 'next_steps',
}

SECTION_TYPE_TO_KEY = {v: k for k, v in SECTION_KEY_MAP.items()}


class ProposalFromJSONSerializer(serializers.Serializer):
    """
    Serializer for creating a proposal from a complete JSON payload.

    Accepts proposal metadata at the top level and a ``sections`` dict
    whose keys are camelCase section names mapped to content_json dicts.
    """

    title = serializers.CharField(max_length=255)
    client_name = serializers.CharField(max_length=255)
    client_email = serializers.EmailField(required=False, default='', allow_blank=True)
    client_phone = serializers.CharField(max_length=30, required=False, default='', allow_blank=True)
    project_type = serializers.CharField(max_length=20, required=False, default='', allow_blank=True)
    market_type = serializers.CharField(max_length=20, required=False, default='', allow_blank=True)
    project_type_custom = serializers.CharField(max_length=100, required=False, default='', allow_blank=True)
    market_type_custom = serializers.CharField(max_length=100, required=False, default='', allow_blank=True)
    language = serializers.ChoiceField(
        choices=BusinessProposal.Language.choices, default='es',
    )
    total_investment = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, default=0,
    )
    currency = serializers.ChoiceField(
        choices=BusinessProposal.Currency.choices, default='COP',
    )
    expires_at = serializers.DateTimeField(required=False, allow_null=True, default=None)
    reminder_days = serializers.IntegerField(required=False, default=10)
    urgency_reminder_days = serializers.IntegerField(required=False, default=15)
    discount_percent = serializers.IntegerField(required=False, default=0)
    sections = serializers.DictField(child=serializers.DictField(), required=True)

    def validate_expires_at(self, value):
        if value is not None:
            from django.utils import timezone
            if value < timezone.now():
                raise serializers.ValidationError(
                    'Expiration date must be in the future.'
                )
        return value

    def validate_sections(self, value):
        if 'general' not in value:
            raise serializers.ValidationError(
                'The sections dict must include a "general" key with at least clientName.'
            )
        general = value['general']
        if not isinstance(general, dict) or not general.get('clientName'):
            raise serializers.ValidationError(
                'sections.general must contain a non-empty "clientName".'
            )
        # Strip _meta helper key if present (template download artifact)
        value.pop('_meta', None)
        return value


class ProposalAlertSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and listing manual proposal alerts.
    """
    client_name = serializers.CharField(source='proposal.client_name', read_only=True)
    proposal_title = serializers.CharField(source='proposal.title', read_only=True)

    class Meta:
        model = ProposalAlert
        fields = (
            'id', 'proposal', 'alert_type', 'message', 'alert_date',
            'is_dismissed', 'created_at', 'client_name', 'proposal_title',
        )
        read_only_fields = ('id', 'created_at', 'client_name', 'proposal_title')


class ProposalShareLinkSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and displaying proposal share links.
    """

    class Meta:
        model = ProposalShareLink
        fields = (
            'id', 'uuid', 'shared_by_name', 'shared_by_email',
            'recipient_name', 'recipient_email',
            'view_count', 'first_viewed_at', 'created_at',
        )
        read_only_fields = (
            'id', 'uuid', 'view_count', 'first_viewed_at', 'created_at',
        )


class ProposalDefaultConfigSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving and updating proposal default configurations.
    """

    class Meta:
        model = ProposalDefaultConfig
        fields = ('id', 'language', 'sections_json', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_language(self, value):
        if value not in ('es', 'en'):
            raise serializers.ValidationError(
                'Language must be "es" or "en".'
            )
        return value

    def validate_sections_json(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError(
                'sections_json must be a JSON array (list).'
            )
        required_keys = {'section_type', 'title', 'order', 'content_json'}
        for i, section in enumerate(value):
            if not isinstance(section, dict):
                raise serializers.ValidationError(
                    f'Each section must be a dict (index {i}).'
                )
            missing = required_keys - set(section.keys())
            if missing:
                raise serializers.ValidationError(
                    f'Section at index {i} is missing keys: {missing}'
                )
        return value


class EmailTemplateConfigSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving and updating email template configurations.
    """

    class Meta:
        model = EmailTemplateConfig
        fields = (
            'id', 'template_key', 'content_overrides', 'is_active',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'template_key', 'created_at', 'updated_at')

    def validate_content_overrides(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                'content_overrides must be a JSON object (dict).'
            )
        return value
