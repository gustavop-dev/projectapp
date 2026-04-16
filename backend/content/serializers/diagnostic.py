"""Serializers for the WebAppDiagnostic feature."""

from rest_framework import serializers

from accounts.models import UserProfile
from accounts.services.proposal_client_service import build_client_display_name
from content.models import DiagnosticDocument, WebAppDiagnostic
from content.services import diagnostic_service


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


class DiagnosticDocumentSerializer(serializers.ModelSerializer):
    rendered_md = serializers.SerializerMethodField()

    class Meta:
        model = DiagnosticDocument
        fields = [
            'id', 'doc_type', 'title', 'content_md', 'rendered_md',
            'is_ready', 'order', 'created_at', 'updated_at',
        ]
        read_only_fields = ['doc_type', 'order', 'rendered_md',
                            'created_at', 'updated_at']

    def get_rendered_md(self, doc):
        # Reuse a context cached on the serializer context when batching docs
        # for the same diagnostic (see DiagnosticDetailSerializer).
        context = self.context.get('render_context')
        return diagnostic_service.render_document(doc, context=context)


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
    documents = serializers.SerializerMethodField()
    payment_terms = serializers.JSONField()
    radiography = serializers.JSONField()

    class Meta(DiagnosticListSerializer.Meta):
        fields = DiagnosticListSerializer.Meta.fields + [
            'payment_terms', 'radiography', 'documents',
        ]

    def get_documents(self, diagnostic):
        render_context = diagnostic_service.build_render_context(diagnostic)
        docs = sorted(diagnostic.documents.all(), key=lambda d: d.order)
        return DiagnosticDocumentSerializer(
            docs, many=True, context={'render_context': render_context},
        ).data


class DiagnosticUpdateSerializer(serializers.ModelSerializer):
    """Admin update payload — supports pricing/radiography edits.

    Status is changed via dedicated send-initial/send-final endpoints.
    """

    class Meta:
        model = WebAppDiagnostic
        fields = [
            'title', 'language',
            'investment_amount', 'currency', 'payment_terms',
            'duration_label', 'size_category', 'radiography',
        ]
        extra_kwargs = {
            'title': {'required': False},
            'language': {'required': False},
        }


class DiagnosticDocumentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticDocument
        fields = ['title', 'content_md', 'is_ready']
        extra_kwargs = {
            'title': {'required': False},
            'content_md': {'required': False},
            'is_ready': {'required': False},
        }


class PublicDiagnosticSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = WebAppDiagnostic
        fields = [
            'uuid', 'title', 'status', 'language',
            'client_name', 'investment_amount', 'currency',
            'duration_label', 'size_category', 'documents',
        ]

    def get_client_name(self, diagnostic):
        return build_client_display_name(diagnostic.client)

    def get_documents(self, diagnostic):
        docs = diagnostic_service.visible_documents(diagnostic)
        if not docs:
            return []
        render_context = diagnostic_service.build_render_context(diagnostic)
        return [
            {
                'id': d.id,
                'doc_type': d.doc_type,
                'title': d.title,
                'order': d.order,
                'rendered_md': diagnostic_service.render_document(d, context=render_context),
            }
            for d in docs
        ]
