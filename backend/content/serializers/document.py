from rest_framework import serializers

from content.models import Document, DocumentFolder, DocumentTag
from content.services.document_archive_service import (
    DocumentArchiveError, ensure_active_target,
)


class _TagSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentTag
        fields = ('id', 'name', 'color')


def _archived_cause(obj):
    """'folder' si lo arrastró el archivado de una carpeta, 'manual' si no."""
    if not obj.is_archived:
        return None
    return 'folder' if obj.archived_via_folder_id else 'manual'


class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for document lists."""

    folder_name = serializers.CharField(source='folder.name', read_only=True, default=None)
    tag_details = _TagSummarySerializer(source='tags', many=True, read_only=True)
    content_excerpt = serializers.SerializerMethodField()
    archived_cause = serializers.SerializerMethodField()

    EXCERPT_MAX_CHARS = 500

    class Meta:
        model = Document
        fields = (
            'id', 'uuid', 'title', 'slug', 'status',
            'client_name', 'language', 'cover_type', 'template_style',
            'include_portada', 'include_subportada', 'include_contraportada',
            'folder', 'folder_name', 'tag_details', 'content_excerpt',
            'created_at', 'updated_at',
            'is_archived', 'archived_at', 'archived_cause',
        )

    def get_archived_cause(self, obj):
        return _archived_cause(obj)

    def get_content_excerpt(self, obj):
        """First ~500 chars of the markdown, cut at the last complete line.

        Feeds the gallery mini-preview so the list payload stays small; the
        frontend closes any dangling code fence before rendering it.
        """
        markdown = obj.content_markdown or ''
        if len(markdown) <= self.EXCERPT_MAX_CHARS:
            return markdown
        cut = markdown[:self.EXCERPT_MAX_CHARS]
        last_newline = cut.rfind('\n')
        if last_newline > 0:
            cut = cut[:last_newline]
        return cut


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Full serializer for document detail view."""

    folder_name = serializers.CharField(source='folder.name', read_only=True, default=None)
    tag_details = _TagSummarySerializer(source='tags', many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        source='tags', many=True, read_only=True,
    )
    archived_cause = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'id', 'uuid', 'title', 'slug', 'status',
            'content_markdown', 'content_json',
            'client_name', 'language', 'cover_type', 'template_style',
            'include_portada', 'include_subportada', 'include_contraportada',
            'folder', 'folder_name', 'tag_ids', 'tag_details',
            'created_at', 'updated_at',
            'is_archived', 'archived_at', 'archived_cause',
        )

    def get_archived_cause(self, obj):
        return _archived_cause(obj)


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
            'title', 'client_name', 'language', 'cover_type', 'template_style',
            'include_portada', 'include_subportada', 'include_contraportada',
            'status', 'content_markdown', 'content_json',
            'folder_id', 'tag_ids',
        )
        extra_kwargs = {
            'title': {'required': True},
            'content_markdown': {'required': False},
            'content_json': {'required': False},
        }

    def validate(self, attrs):
        """Impide dejar un documento activo dentro de una carpeta archivada.

        Va a nivel de objeto y no de campo porque la regla depende del estado
        de la propia instancia: mover un documento YA archivado entre carpetas
        es un caso soportado.
        """
        if 'folder' in attrs:
            try:
                ensure_active_target(
                    attrs['folder'],
                    moving_archived=bool(self.instance and self.instance.is_archived),
                )
            except DocumentArchiveError as exc:
                raise serializers.ValidationError({'folder_id': str(exc)}) from exc
        return attrs

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
    template_style = serializers.ChoiceField(
        choices=Document.TemplateStyle.choices, required=False,
        default='professional',
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

    def validate_folder_id(self, value):
        """Un documento nuevo nace activo: su carpeta tiene que estarlo también."""
        try:
            ensure_active_target(value)
        except DocumentArchiveError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value
