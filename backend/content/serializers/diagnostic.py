"""Serializers for the WebAppDiagnostic feature."""

from rest_framework import serializers

from accounts.models import UserProfile
from accounts.services.proposal_client_service import build_client_display_name
from content.models import (
    DiagnosticAttachment,
    DiagnosticChangeLog,
    DiagnosticSection,
    WebAppDiagnostic,
)
from content.services import diagnostic_service

# Whitelist of render_context keys that are safe to expose on the public
# client-facing endpoint. Everything else (e.g. controllers_disconnected,
# *_count raw numbers used only for admin-facing hints) stays admin-only.
PUBLIC_RENDER_CONTEXT_KEYS = frozenset({
    'client_name',
    'investment_amount',
    'currency',
    'payment_initial_pct',
    'payment_final_pct',
    'duration_label',
    'size_category_label',
    'stack_backend_name',
    'stack_backend_version',
    'stack_frontend_name',
    'stack_frontend_version',
    'entities_count', 'entities_size',
    'routes_total', 'routes_size',
    'frontend_routes_count', 'frontend_routes_size',
    'components_count', 'components_size',
    'external_integrations', 'integrations_size',
    'modules_count', 'modules_size', 'modules_list',
})


def _render_context_for(serializer, diagnostic):
    """Build-or-reuse the render_context dict scoped to one serializer instance.

    Avoids recomputing ``build_render_context`` for multiple SerializerMethodFields
    on the same detail response.
    """
    cached = getattr(serializer, '_cached_render_context', None)
    if cached is None:
        cached = diagnostic_service.build_render_context(diagnostic)
        serializer._cached_render_context = cached
    return cached


class _ClientSummarySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    company = serializers.CharField(source='company_name')

    class Meta:
        model = UserProfile
        fields = ['id', 'name', 'email', 'company']

    def get_name(self, profile):
        return build_client_display_name(profile)

    def get_email(self, profile):
        return profile.user.email or ''


class DiagnosticSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticSection
        fields = [
            'id', 'section_type', 'title', 'order', 'is_enabled',
            'visibility', 'content_json',
        ]
        read_only_fields = ['section_type']


class DiagnosticSectionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticSection
        fields = ['title', 'order', 'is_enabled', 'visibility', 'content_json']
        extra_kwargs = {
            'title': {'required': False},
            'order': {'required': False},
            'is_enabled': {'required': False},
            'visibility': {'required': False},
            'content_json': {'required': False},
        }


class DiagnosticChangeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticChangeLog
        fields = [
            'id', 'change_type', 'field_name', 'old_value', 'new_value',
            'description', 'actor_type', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


def serialize_diagnostic_attachment(att):
    display = (
        att.custom_type_label
        if att.document_type == DiagnosticAttachment.DOC_TYPE_OTHER
        and att.custom_type_label
        else att.get_document_type_display()
    )
    return {
        'id': att.id,
        'document_type': att.document_type,
        'document_type_display': display,
        'custom_type_label': att.custom_type_label,
        'title': att.title,
        'file': att.file.url if att.file else None,
        'uploaded_by_name': (
            att.uploaded_by.get_full_name() or att.uploaded_by.username
            if att.uploaded_by else ''
        ),
        'created_at': att.created_at.isoformat(),
    }


class DiagnosticListSerializer(serializers.ModelSerializer):
    client = _ClientSummarySerializer(read_only=True)
    public_url = serializers.CharField(read_only=True)

    class Meta:
        model = WebAppDiagnostic
        fields = [
            'id', 'uuid', 'title', 'status', 'language',
            'client', 'public_url',
            'investment_amount', 'currency', 'duration_label',
            'size_category',
            'view_count', 'last_viewed_at',
            'initial_sent_at', 'final_sent_at', 'responded_at',
            'created_at', 'updated_at',
        ]


class DiagnosticDetailSerializer(DiagnosticListSerializer):
    sections = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    change_logs = serializers.SerializerMethodField()
    payment_terms = serializers.JSONField()
    radiography = serializers.JSONField()
    render_context = serializers.SerializerMethodField()

    class Meta(DiagnosticListSerializer.Meta):
        fields = DiagnosticListSerializer.Meta.fields + [
            'payment_terms', 'radiography',
            'sections', 'attachments', 'change_logs', 'render_context',
        ]

    def get_sections(self, diagnostic):
        # Model Meta.ordering = ['order'] already sorts; use list() to consume
        # the prefetched cache.
        return DiagnosticSectionSerializer(
            list(diagnostic.sections.all()), many=True,
        ).data

    def get_attachments(self, diagnostic):
        return [
            serialize_diagnostic_attachment(att)
            for att in diagnostic.attachments.all()
        ]

    def get_change_logs(self, diagnostic):
        # Slice the prefetched list in Python to keep the cache intact; an
        # upstream `RelatedManager[:60]` would issue a fresh SQL query.
        return DiagnosticChangeLogSerializer(
            list(diagnostic.change_logs.all())[:60], many=True,
        ).data

    def get_render_context(self, diagnostic):
        return _render_context_for(self, diagnostic)


class DiagnosticUpdateSerializer(serializers.ModelSerializer):
    """Admin update payload — pricing/radiography/client edits."""

    client_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.filter(role=UserProfile.ROLE_CLIENT),
        source='client',
        write_only=True,
        required=False,
        allow_null=False,
    )

    class Meta:
        model = WebAppDiagnostic
        fields = [
            'title', 'language',
            'investment_amount', 'currency', 'payment_terms',
            'duration_label', 'size_category', 'radiography',
            'client_id',
        ]
        extra_kwargs = {
            'title': {'required': False},
            'language': {'required': False},
        }


class PublicDiagnosticSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()
    render_context = serializers.SerializerMethodField()

    class Meta:
        model = WebAppDiagnostic
        fields = [
            'uuid', 'title', 'status', 'language',
            'client_name', 'investment_amount', 'currency',
            'duration_label', 'size_category',
            'initial_sent_at', 'final_sent_at', 'responded_at',
            'sections', 'render_context',
        ]

    def get_client_name(self, diagnostic):
        return build_client_display_name(diagnostic.client)

    def get_sections(self, diagnostic):
        return DiagnosticSectionSerializer(
            diagnostic_service.visible_sections(diagnostic),
            many=True,
        ).data

    def get_render_context(self, diagnostic):
        full = _render_context_for(self, diagnostic)
        return {k: v for k, v in full.items() if k in PUBLIC_RENDER_CONTEXT_KEYS}
