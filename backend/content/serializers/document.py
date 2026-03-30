from rest_framework import serializers

from content.models import Document


class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for document lists."""

    class Meta:
        model = Document
        fields = (
            'id', 'uuid', 'title', 'slug', 'status',
            'client_name', 'language', 'cover_type',
            'include_portada', 'include_subportada', 'include_contraportada',
            'created_at', 'updated_at',
        )


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Full serializer for document detail view."""

    class Meta:
        model = Document
        fields = (
            'id', 'uuid', 'title', 'slug', 'status',
            'content_markdown', 'content_json',
            'client_name', 'language', 'cover_type',
            'include_portada', 'include_subportada', 'include_contraportada',
            'created_at', 'updated_at',
        )


class DocumentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating documents."""

    class Meta:
        model = Document
        fields = (
            'title', 'client_name', 'language', 'cover_type',
            'include_portada', 'include_subportada', 'include_contraportada',
            'status', 'content_markdown', 'content_json',
        )
        extra_kwargs = {
            'title': {'required': True},
            'content_markdown': {'required': False},
            'content_json': {'required': False},
        }


class DocumentFromMarkdownSerializer(serializers.Serializer):
    """Serializer for creating a document from markdown input."""

    title = serializers.CharField(max_length=255)
    markdown = serializers.CharField(required=True)
    client_name = serializers.CharField(max_length=255, required=False, default='')
    language = serializers.ChoiceField(
        choices=Document.Language.choices, required=False, default='es',
    )
    cover_type = serializers.ChoiceField(
        choices=Document.CoverType.choices, required=False, default='generic',
    )
    include_portada = serializers.BooleanField(required=False, default=True)
    include_subportada = serializers.BooleanField(required=False, default=True)
    include_contraportada = serializers.BooleanField(required=False, default=True)
