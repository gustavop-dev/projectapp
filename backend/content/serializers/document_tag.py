from rest_framework import serializers

from content.models import DocumentTag


class DocumentTagSerializer(serializers.ModelSerializer):
    """Serializer for document tags."""

    class Meta:
        model = DocumentTag
        fields = (
            'id', 'name', 'slug', 'color',
            'created_at', 'updated_at',
        )
        read_only_fields = ('slug', 'created_at', 'updated_at')
