"""Serializers for the client-facing document portal (platform / JWT)."""

from rest_framework import serializers

from content.models import Document


class ClientDocumentSerializer(serializers.ModelSerializer):
    """Read-only view of a Document for the owning client."""

    document_type_code = serializers.CharField(
        source='document_type.code', read_only=True, default='',
    )
    signed = serializers.SerializerMethodField()
    signed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'uuid', 'title', 'slug', 'language', 'status',
            'document_type_code', 'requires_signature',
            'signed', 'signed_at', 'signed_by_name', 'signature_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_signed(self, obj):
        return obj.signed_at is not None

    def get_signed_by_name(self, obj):
        signer = obj.signed_by
        if signer is None:
            return obj.signature_name or ''
        full = f'{signer.first_name} {signer.last_name}'.strip()
        return full or signer.email or ''
