"""Serializers for the public financing program and admin agreement workspace."""

from rest_framework import serializers

from accounts.models import Project, UserProfile
from content.models import (
    BusinessProposal,
    FinancingAgreement,
    FinancingAgreementEvent,
    FinancingAgreementTemplate,
)
from content.services.financing_agreement_service import allowed_actions


class FinancingAgreementTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancingAgreementTemplate
        fields = (
            'id', 'name', 'version', 'content_markdown', 'is_default',
            'is_active', 'created_at', 'updated_at',
        )
        read_only_fields = fields


class FinancingAgreementWriteSerializer(serializers.Serializer):
    client_id = serializers.PrimaryKeyRelatedField(
        source='client',
        queryset=UserProfile.objects.clients(),
        required=False,
    )
    source_proposal_id = serializers.PrimaryKeyRelatedField(
        source='source_proposal',
        queryset=BusinessProposal.objects.all(),
        allow_null=True,
        required=False,
    )
    source_project_id = serializers.PrimaryKeyRelatedField(
        source='source_project',
        queryset=Project.objects.all(),
        allow_null=True,
        required=False,
    )
    template_id = serializers.PrimaryKeyRelatedField(
        source='template',
        queryset=FinancingAgreementTemplate.objects.filter(is_active=True),
        required=False,
    )

    client_full_name = serializers.CharField(
        max_length=311, required=False, allow_blank=True, trim_whitespace=True,
    )
    client_company = serializers.CharField(
        max_length=200, required=False, allow_blank=True, trim_whitespace=True,
    )
    client_id_type = serializers.CharField(
        max_length=20, required=False, allow_blank=True, trim_whitespace=True,
    )
    client_id_number = serializers.CharField(
        max_length=32, required=False, allow_blank=True, trim_whitespace=True,
    )
    client_email = serializers.EmailField(required=False, allow_blank=True)
    client_phone = serializers.CharField(
        max_length=30, required=False, allow_blank=True, trim_whitespace=True,
    )
    original_contract_reference = serializers.CharField(
        max_length=255, required=False, trim_whitespace=True,
    )
    original_contract_date = serializers.DateField(required=False)
    project_name = serializers.CharField(
        max_length=255, required=False, trim_whitespace=True,
    )
    financed_scope = serializers.CharField(
        required=False, allow_blank=True, trim_whitespace=True,
    )
    modality = serializers.ChoiceField(
        choices=FinancingAgreement.Modality.choices,
        required=False,
    )
    partnership_start_date = serializers.DateField(required=False)
    currency = serializers.ChoiceField(
        choices=(('COP', 'COP'), ('USD', 'USD')),
        required=False,
    )
    total_value = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, required=False,
    )
    initial_payment = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, required=False,
    )
    hosting_value = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, required=False,
    )
    hosting_period = serializers.ChoiceField(
        choices=FinancingAgreement.HostingPeriod.choices,
        required=False,
    )
    first_installment_date = serializers.DateField(required=False, write_only=True)
    installment_schedule = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )
    contract_markdown = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        if self.instance is None:
            required = {
                'client': 'Selecciona un cliente.',
                'original_contract_reference': 'Indica la referencia del contrato original.',
                'original_contract_date': 'Indica la fecha del contrato original.',
                'project_name': 'Indica el proyecto o producto.',
                'financed_scope': 'Describe el alcance que se financiará.',
                'modality': 'Selecciona una modalidad.',
                'partnership_start_date': 'Indica el inicio de la alianza.',
                'total_value': 'Indica el valor total.',
                'hosting_value': 'Indica el costo vigente del Hosting.',
            }
            errors = {
                key if key != 'client' else 'client_id': [message]
                for key, message in required.items()
                if key not in attrs
            }
            if errors:
                raise serializers.ValidationError(errors)
        return attrs


class FinancingAgreementListSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client_full_name', read_only=True)
    modality_label = serializers.CharField(source='get_modality_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    allowed_actions = serializers.SerializerMethodField()
    has_signed_document = serializers.SerializerMethodField()
    previous_agreement_number = serializers.CharField(
        source='previous_agreement.number',
        read_only=True,
        allow_null=True,
    )
    second_cycle_id = serializers.SerializerMethodField()

    class Meta:
        model = FinancingAgreement
        fields = (
            'id', 'uuid', 'number', 'client', 'client_name', 'client_company',
            'project_name', 'modality', 'modality_label', 'cycle_number',
            'previous_agreement', 'previous_agreement_number', 'second_cycle_id',
            'partnership_start_date', 'partnership_end_date', 'currency',
            'total_value', 'initial_payment', 'financed_balance',
            'hosting_value', 'hosting_period', 'status', 'status_label',
            'template_name', 'template_version', 'has_signed_document',
            'allowed_actions', 'is_archived', 'archived_at', 'created_at',
            'updated_at',
        )

    def get_allowed_actions(self, obj):
        return allowed_actions(obj)

    def get_has_signed_document(self, obj):
        return bool(obj.signed_document)

    def get_second_cycle_id(self, obj):
        try:
            return obj.second_cycle.pk
        except FinancingAgreement.DoesNotExist:
            return None


class FinancingAgreementEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = FinancingAgreementEvent
        fields = (
            'id', 'event_type', 'actor', 'actor_name', 'before_state',
            'after_state', 'details', 'created_at',
        )

    def get_actor_name(self, obj):
        if not obj.actor:
            return 'Sistema'
        return obj.actor.get_full_name() or obj.actor.get_username()


class FinancingAgreementDetailSerializer(FinancingAgreementListSerializer):
    events = FinancingAgreementEventSerializer(many=True, read_only=True)
    template = FinancingAgreementTemplateSerializer(read_only=True)
    ready_by_name = serializers.SerializerMethodField()
    activated_by_name = serializers.SerializerMethodField()
    completed_by_name = serializers.SerializerMethodField()
    cancelled_by_name = serializers.SerializerMethodField()

    class Meta(FinancingAgreementListSerializer.Meta):
        fields = FinancingAgreementListSerializer.Meta.fields + (
            'source_proposal', 'source_project', 'client_full_name',
            'client_id_type', 'client_id_number', 'client_email', 'client_phone',
            'original_contract_reference', 'original_contract_date',
            'financed_scope', 'installment_schedule', 'template',
            'contract_markdown', 'resolved_contract_markdown',
            'resolved_contract_sha256', 'signed_document_sha256',
            'signed_document_size', 'ready_at', 'ready_by', 'ready_by_name',
            'activated_at', 'activated_by', 'activated_by_name', 'completed_at',
            'completed_by', 'completed_by_name', 'completion_note',
            'cancelled_at', 'cancelled_by', 'cancelled_by_name',
            'cancellation_reason', 'second_cycle_approved_at',
            'second_cycle_approved_by', 'events',
        )

    @staticmethod
    def _actor_name(user):
        if not user:
            return ''
        return user.get_full_name() or user.get_username()

    def get_ready_by_name(self, obj):
        return self._actor_name(obj.ready_by)

    def get_activated_by_name(self, obj):
        return self._actor_name(obj.activated_by)

    def get_completed_by_name(self, obj):
        return self._actor_name(obj.completed_by)

    def get_cancelled_by_name(self, obj):
        return self._actor_name(obj.cancelled_by)
