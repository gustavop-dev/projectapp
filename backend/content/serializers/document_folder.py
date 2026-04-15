from rest_framework import serializers

from content.models import DocumentFolder


class DocumentFolderSerializer(serializers.ModelSerializer):
    """Serializer for document folders (flat, inline-managed).

    `document_count` is read from a queryset annotation when provided by the
    caller; otherwise it falls back to a per-folder COUNT query so single-object
    responses (create/update) still include the field.
    """

    document_count = serializers.SerializerMethodField()

    class Meta:
        model = DocumentFolder
        fields = (
            'id', 'name', 'slug', 'order',
            'document_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('slug', 'created_at', 'updated_at')

    def get_document_count(self, obj):
        value = getattr(obj, 'document_count', None)
        if isinstance(value, int):
            return value
        return obj.documents.count()
