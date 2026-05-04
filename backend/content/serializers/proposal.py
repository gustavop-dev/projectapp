from rest_framework import serializers

from accounts.models import UserProfile
from accounts.services import proposal_client_service
from content.services.proposal_module_links import (
    normalize_technical_document_module_links,
)
from content.models import (
    BusinessProposal,
    EmailTemplateConfig,
    ProposalAlert,
    ProposalProjectStage,
    ProposalSection,
    ProposalRequirementGroup,
    ProposalRequirementItem,
    ProposalShareLink,
    ProposalDefaultConfig,
)
from content.serializers.proposal_clients import ProposalClientSerializer
from content.utils import validate_editable_slug, validate_email_domain_mx


def _validate_client_email_mx(value):
    """Shared field validator: reject emails whose domain has no MX/A records."""
    if value and not validate_email_domain_mx(value):
        raise serializers.ValidationError(
            'El dominio de este correo no puede recibir emails (sin registros MX).'
        )
    return value


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


class ProposalProjectStageSerializer(serializers.ModelSerializer):
    """
    Serializer for ProposalProjectStage — internal project execution tracking.

    Exposes the stage dates + completion + alert timestamps. Used by the
    admin Cronograma tab to read stage state. Writes go through the
    dedicated update_project_stage / complete_project_stage endpoints,
    not through ProposalDetailSerializer (which is read-only for stages).
    """
    stage_label = serializers.CharField(source='get_stage_key_display', read_only=True)

    class Meta:
        model = ProposalProjectStage
        fields = (
            'id', 'stage_key', 'stage_label', 'order',
            'start_date', 'end_date', 'completed_at',
            'warning_sent_at', 'last_overdue_reminder_at',
            'created_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'stage_label', 'completed_at',
            'warning_sent_at', 'last_overdue_reminder_at',
            'created_at', 'updated_at',
        )

    def validate(self, attrs):
        start = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end = attrs.get('end_date', getattr(self.instance, 'end_date', None))
        if start and end and start > end:
            raise serializers.ValidationError({
                'end_date': 'La fecha fin debe ser igual o posterior a la fecha de inicio.',
            })
        return attrs


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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # The investment section's hostingPlan mirrors fields that live on
        # BusinessProposal (hosting_percent, hosting_discount_*). Normalize
        # here so every consumer — public UI, PDF renderer, platform
        # onboarding — reads the same numbers without re-implementing the
        # override locally.
        if (instance.section_type == 'investment'
                and isinstance(data.get('content_json'), dict)):
            from content.services.proposal_service import normalize_hosting_plan
            cj = data['content_json']
            if isinstance(cj.get('hostingPlan'), dict):
                cj['hostingPlan'] = normalize_hosting_plan(
                    instance.proposal, cj['hostingPlan']
                )
        return data


class ProposalListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing proposals in admin views.
    Includes computed fields for expiration status.
    """
    days_remaining = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    available_transitions = serializers.SerializerMethodField()
    client = ProposalClientSerializer(read_only=True)

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
            'available_transitions', 'language', 'sent_at',
            'client',
        )

    def get_days_remaining(self, obj):
        return obj.days_remaining

    def get_is_expired(self, obj):
        return obj.is_expired

    def get_available_transitions(self, obj):
        return obj.available_transitions


class ProposalDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for a business proposal, used by both client and admin detail views.

    Includes nested sections (filtered by is_enabled for client, all for admin),
    nested requirement groups with items, and computed properties.
    """
    sections = serializers.SerializerMethodField()
    requirement_groups = ProposalRequirementGroupSerializer(many=True, read_only=True)
    # project_stages is internal-only execution tracking; the model docstring
    # explicitly says it must never be rendered to the client. Gate by is_admin.
    project_stages = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    public_url = serializers.SerializerMethodField()
    discounted_investment = serializers.SerializerMethodField()
    effective_total_investment = serializers.SerializerMethodField()
    has_confirmed_module_selection = serializers.ReadOnlyField()
    available_transitions = serializers.SerializerMethodField()
    proposal_documents = serializers.SerializerMethodField()
    client = ProposalClientSerializer(read_only=True)

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
            'sections', 'requirement_groups', 'project_stages', 'change_logs',
            'days_remaining', 'is_expired', 'public_url',
            'discounted_investment', 'effective_total_investment',
            'selected_modules', 'has_confirmed_module_selection',
            'contract_params', 'available_transitions', 'proposal_documents',
            'platform_onboarding_completed_at',
            'platform_onboarding_status',
            'client',
        )

    def get_project_stages(self, obj):
        """Return project_stages only for admin requests; empty for public."""
        if not self.context.get('is_admin', False):
            return []
        stages = obj.project_stages.all()
        return ProposalProjectStageSerializer(stages, many=True).data

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
                'field_name': log.field_name,
                'old_value': log.old_value,
                'new_value': log.new_value,
                'actor_type': log.actor_type,
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

    def get_effective_total_investment(self, obj):
        """
        Client-facing total: base ``total_investment`` plus the price of
        the additional calculator modules in the client's selection, with
        a fallback to admin-marked defaults when the client hasn't
        confirmed the calculator yet. Same rule as the PDF and the admin
        metrics map so every consumer sees the same number.
        """
        # Deferred import — views/proposal.py imports from this module at
        # load time, so a top-level import would be circular.
        from content.views.proposal import _effective_total_for_proposal
        return str(_effective_total_for_proposal(obj))

    def get_available_transitions(self, obj):
        return obj.available_transitions

    def get_proposal_documents(self, obj):
        is_admin = self.context.get('is_admin', False)
        if not is_admin:
            return []
        docs = obj.proposal_documents.all().order_by('-created_at')
        return [serialize_proposal_document(d) for d in docs]


class ContractParamsSerializer(serializers.Serializer):
    """Validate contract_params before saving to the JSONField."""

    CONTRACT_SOURCE_CHOICES = ('default', 'custom')

    contract_source = serializers.ChoiceField(
        choices=CONTRACT_SOURCE_CHOICES, default='default',
    )
    client_full_name = serializers.CharField(max_length=255, required=False, default='')
    client_cedula = serializers.CharField(max_length=30)
    client_email = serializers.EmailField(required=False, default='')
    contractor_full_name = serializers.CharField(max_length=255, required=False, default='')
    contractor_cedula = serializers.CharField(max_length=30, required=False, default='')
    contractor_email = serializers.EmailField(required=False, default='')
    bank_name = serializers.CharField(max_length=100, required=False, default='')
    bank_account_type = serializers.ChoiceField(
        choices=('Ahorros', 'Corriente'), default='Ahorros', required=False,
    )
    bank_account_number = serializers.CharField(max_length=50, required=False, default='')
    contract_city = serializers.CharField(max_length=100, required=False, default='Medellín')
    contract_date = serializers.CharField(max_length=20, required=False, default='')
    custom_contract_markdown = serializers.CharField(required=False, default='')

    def validate(self, data):
        if data.get('contract_source') == 'custom' and not data.get('custom_contract_markdown'):
            raise serializers.ValidationError(
                {'custom_contract_markdown': 'Required when contract_source is "custom".'}
            )
        return data


def serialize_proposal_document(d):
    """Serialize a ProposalDocument instance to a dict. Used by views and serializers."""
    display = (
        d.custom_type_label
        if d.document_type == 'other' and d.custom_type_label
        else d.get_document_type_display()
    )
    return {
        'id': d.id,
        'document_type': d.document_type,
        'document_type_display': display,
        'custom_type_label': d.custom_type_label,
        'title': d.title,
        'file': d.file.url if d.file else None,
        'is_generated': d.is_generated,
        'created_at': d.created_at.isoformat(),
    }


class ProposalCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating business proposal metadata.

    Client identity is canonical on ``BusinessProposal.client`` (FK to
    ``accounts.UserProfile``). The legacy ``client_name``/``client_email``/
    ``client_phone`` fields remain as write-through snapshots, kept in sync
    via ``proposal_client_service.sync_snapshot()``.

    Write contract:
        - ``client_id``: optional FK to an existing ``UserProfile``
          (role=client). When provided, that profile is used as-is and the
          inline ``client_name``/``client_email``/``client_phone``/``client_company``
          values are ignored — the snapshot is rebuilt from the profile.
        - When ``client_id`` is omitted/null, the service is asked to
          ``get_or_create`` a profile from the inline fields. Empty email
          triggers placeholder generation.
        - ``propagate_client_updates``: write-only boolean. When ``true``
          AND a client is being updated inline, the service propagates the
          new values to the ``UserProfile`` (cascading to all linked
          proposals). Default ``false``.
    """

    client_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.clients(),
        source='client',
        write_only=True,
        required=False,
        allow_null=True,
    )
    client_company = serializers.CharField(
        write_only=True, required=False, allow_blank=True, max_length=200, default='',
    )
    propagate_client_updates = serializers.BooleanField(
        write_only=True, required=False, default=False,
    )
    client = ProposalClientSerializer(read_only=True)

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
            'client_id', 'client_company', 'propagate_client_updates', 'client',
        )

    def validate_client_email(self, value):
        return _validate_client_email_mx(value)

    def validate_slug(self, value):
        return validate_editable_slug(
            value, BusinessProposal, self.instance, conflict_phrase='otra propuesta',
        )

    def validate_expires_at(self, value):
        """Ensure expiration date is in the future when actually being changed.

        Allow re-saving a proposal with its existing (possibly past) ``expires_at``
        unchanged so admins can edit other fields on an expired proposal.
        """
        if value is None:
            return value
        from django.utils import timezone
        existing = getattr(self.instance, 'expires_at', None)
        if existing is not None and existing == value:
            return value
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

    # ------------------------------------------------------------------
    # client FK resolution + snapshot sync
    # ------------------------------------------------------------------

    def _pop_client_inputs(self, validated_data):
        """Strip client-related inputs from validated_data; return as dict."""
        return {
            'client': validated_data.pop('client', None),
            'name': validated_data.get('client_name', ''),
            'email': validated_data.get('client_email', ''),
            'phone': validated_data.get('client_phone', ''),
            'company': validated_data.pop('client_company', ''),
            'propagate': validated_data.pop('propagate_client_updates', False),
        }

    def create(self, validated_data):
        client_inputs = self._pop_client_inputs(validated_data)
        profile = client_inputs['client']
        if profile is None:
            profile = proposal_client_service.get_or_create_client_for_proposal(
                name=client_inputs['name'],
                email=client_inputs['email'],
                phone=client_inputs['phone'],
                company=client_inputs['company'],
            )
        validated_data['client'] = profile
        proposal = super().create(validated_data)
        proposal_client_service.sync_snapshot(proposal)
        return proposal

    def update(self, instance, validated_data):
        client_inputs = self._pop_client_inputs(validated_data)
        explicit_profile = client_inputs['client']

        # If caller passed a client_id, switch the FK and skip auto-create.
        if explicit_profile is not None:
            validated_data['client'] = explicit_profile
        # Otherwise: keep the current FK; the snapshot fields may still be
        # edited inline (overrides for THIS proposal only).

        # Optional propagation: when the admin opted in via the checkbox,
        # push the inline edits up to the canonical UserProfile so all other
        # proposals stay in sync.
        if client_inputs['propagate']:
            target = explicit_profile or instance.client
            if target is not None:
                proposal_client_service.update_client_profile(
                    target,
                    name=client_inputs['name'] or None,
                    email=client_inputs['email'] or None,
                    phone=client_inputs['phone'] or None,
                    company=client_inputs['company'] or None,
                )

        proposal = super().update(instance, validated_data)

        # When we just switched FK or propagated upstream, reset the snapshot
        # so this proposal mirrors the canonical client identity.
        if explicit_profile is not None or client_inputs['propagate']:
            proposal_client_service.sync_snapshot(proposal)

        return proposal


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
        if (
            self.instance
            and self.instance.section_type == ProposalSection.SectionType.TECHNICAL_DOCUMENT
        ):
            sections = [
                {
                    'section_type': section.section_type,
                    'content_json': value if section.pk == self.instance.pk else section.content_json,
                }
                for section in self.instance.proposal.sections.all()
            ]
            return normalize_technical_document_module_links(value, sections)
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
    'technicalDocument': 'technical_document',
    'valueAddedModules': 'value_added_modules',
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

    def validate_client_email(self, value):
        return _validate_client_email_mx(value)

    def validate_expires_at(self, value):
        """Allow keeping the existing expires_at unchanged when re-importing JSON.

        Bound proposal is passed via context so we can compare against the
        currently stored value and skip the future-only check when nothing
        is actually being changed.
        """
        if value is None:
            return value
        from django.utils import timezone
        proposal = self.context.get('proposal')
        existing = getattr(proposal, 'expires_at', None) if proposal else None
        if existing is not None and existing == value:
            return value
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
        fields = (
            'id',
            'language',
            'sections_json',
            'default_currency',
            'default_total_investment',
            'hosting_percent',
            'hosting_discount_semiannual',
            'hosting_discount_quarterly',
            'expiration_days',
            'reminder_days',
            'urgency_reminder_days',
            'default_discount_percent',
            'default_slug_pattern',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'hosting_percent': {'min_value': 0, 'max_value': 100},
            'hosting_discount_semiannual': {'min_value': 0, 'max_value': 100},
            'hosting_discount_quarterly': {'min_value': 0, 'max_value': 100},
            'default_discount_percent': {'min_value': 0, 'max_value': 100},
            'reminder_days': {'min_value': 0, 'max_value': 365},
            'urgency_reminder_days': {'min_value': 0, 'max_value': 365},
            'default_total_investment': {'min_value': 0},
        }

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
        normalized_sections = []
        technical_content = None
        for section in value:
            cloned = dict(section)
            content_json = cloned.get('content_json')
            cloned['content_json'] = content_json if isinstance(content_json, dict) else {}
            if cloned.get('section_type') == ProposalSection.SectionType.TECHNICAL_DOCUMENT:
                technical_content = cloned['content_json']
            normalized_sections.append(cloned)

        if technical_content is not None:
            canonical_technical = normalize_technical_document_module_links(
                technical_content,
                normalized_sections,
            )
            normalized_sections = [
                {
                    **section,
                    'content_json': canonical_technical
                    if section.get('section_type') == ProposalSection.SectionType.TECHNICAL_DOCUMENT
                    else section['content_json'],
                }
                for section in normalized_sections
            ]
            return normalized_sections
        return value

    def validate_expiration_days(self, value):
        if value < 1 or value > 365:
            raise serializers.ValidationError(
                'expiration_days must be between 1 and 365.'
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
