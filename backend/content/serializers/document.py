from rest_framework import serializers

from content.models import Document, DocumentFolder, DocumentTag


class _TagSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentTag
        fields = ('id', 'name', 'color')


class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for document lists."""

    folder_name = serializers.CharField(source='folder.name', read_only=True, default=None)
    tag_details = _TagSummarySerializer(source='tags', many=True, read_only=True)

    class Meta:
        model = Document
        fields = (
            'id', 'uuid', 'title', 'slug', 'status',
            'client_name', 'language', 'cover_type',
            'include_portada', 'include_subportada', 'include_contraportada',
            'folder', 'folder_name', 'tag_details',
            'created_at', 'updated_at',
        )


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Full serializer for document detail view."""

    folder_name = serializers.CharField(source='folder.name', read_only=True, default=None)
    tag_details = _TagSummarySerializer(source='tags', many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        source='tags', many=True, read_only=True,
    )

    class Meta:
        model = Document
        fields = (
            'id', 'uuid', 'title', 'slug', 'status',
            'content_markdown', 'content_json',
            'client_name', 'language', 'cover_type',
            'include_portada', 'include_subportada', 'include_contraportada',
            'folder', 'folder_name', 'tag_ids', 'tag_details',
            'created_at', 'updated_at',
        )


class DocumentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating documents."""

    folder_id = serializers.PrimaryKeyRelatedField(
        source='folder', queryset=DocumentFolder.objects.all(),
        required=False, allow_null=True,
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=DocumentTag.objects.all(), many=True, required=False,
    )

    class Meta:
        model = Document
        fields = (
            'title', 'client_name', 'language', 'cover_type',
            'include_portada', 'include_subportada', 'include_contraportada',
            'status', 'content_markdown', 'content_json',
            'folder_id', 'tag_ids',
        )
        extra_kwargs = {
            'title': {'required': True},
            'content_markdown': {'required': False},
            'content_json': {'required': False},
        }

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        document = super().create(validated_data)
        if tag_ids is not None:
            document.tags.set(tag_ids)
        return document

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        document = super().update(instance, validated_data)
        if tag_ids is not None:
            document.tags.set(tag_ids)
        return document


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
    folder_id = serializers.PrimaryKeyRelatedField(
        queryset=DocumentFolder.objects.all(), required=False, allow_null=True,
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=DocumentTag.objects.all(), many=True, required=False,
    )
