from rest_framework import serializers

from accounts.models import Project, UserProfile
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


def apply_client_project_association(attrs, instance=None):
    """Resuelve el trío client/project/client_name manteniendo el invariante.

    Regla única para todas las vías de escritura del panel: un documento con
    proyecto siempre pertenece al cliente del proyecto. `client` llega como
    UserProfile (el vocabulario del panel) y se persiste como `client_user`
    (auth.User, lo que ya escriben las cuentas de cobro y lee el portal).
    Elegir proyecto sin cliente lo deriva; un par inconsistente se rechaza con
    error en `project`; cambiar de cliente sin reasignar el proyecto lo
    desvincula (patrón income). `client_name` se autocompleta con el display
    name sólo cuando el cliente cambia y no vino un valor propio: un texto
    personalizado sobrevive a los saves que no tocan la asociación.
    """
    from accounts.services.proposal_client_service import build_client_display_name
    from content.serializers.accounting import validate_project_client_match

    client_sent = 'client' in attrs
    if client_sent:
        profile = attrs.pop('client')
        attrs['client_user'] = profile.user if profile else None

    previous_client = instance.client_user if instance else None
    if (
        instance is not None
        and client_sent
        and 'project' not in attrs
        and attrs['client_user'] != previous_client
    ):
        attrs['project'] = None

    project = attrs.get('project', instance.project if instance else None)
    client_user = attrs['client_user'] if 'client_user' in attrs else previous_client

    if project is not None and client_user is None:
        attrs['client_user'] = project.client
        client_user = project.client

    client_profile = getattr(client_user, 'profile', None) if client_user else None
    if project is not None and client_profile is not None:
        validate_project_client_match(project, client_profile)

    new_client = attrs.get('client_user')
    client_changed = (
        instance is None
        or instance.client_user_id != getattr(new_client, 'pk', None)
    )
    if (
        'client_user' in attrs
        and new_client is not None
        and client_changed
        and not attrs.get('client_name')
        and client_profile is not None
    ):
        attrs['client_name'] = build_client_display_name(client_profile)
    return attrs


class ClientProjectReadMixin:
    """Campos de asociación compartidos por los serializers de lectura.

    `client` habla en pk de UserProfile — el vocabulario de todo el panel —
    aunque el modelo persista `client_user` (auth.User): la conversión vive
    acá y no en cada consumidor.
    """

    def get_client(self, obj):
        profile = self._client_profile(obj)
        return profile.id if profile else None

    def get_client_display_name(self, obj):
        profile = self._client_profile(obj)
        if profile is None:
            return None
        from accounts.services.proposal_client_service import (
            build_client_display_name,
        )
        return build_client_display_name(profile)

    @staticmethod
    def _client_profile(obj):
        if not obj.client_user_id:
            return None
        return getattr(obj.client_user, 'profile', None)


class DocumentListSerializer(ClientProjectReadMixin, serializers.ModelSerializer):
    """Lightweight serializer for document lists."""

    folder_name = serializers.CharField(source='folder.name', read_only=True, default=None)
    tag_details = _TagSummarySerializer(source='tags', many=True, read_only=True)
    content_excerpt = serializers.SerializerMethodField()
    archived_cause = serializers.SerializerMethodField()
    client = serializers.SerializerMethodField()
    client_display_name = serializers.SerializerMethodField()
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)
    # The documents UI locks issued cuentas; both fields feed that branch.
    document_type_code = serializers.CharField(
        source='document_type.code', read_only=True, default=None,
    )

    EXCERPT_MAX_CHARS = 500

    class Meta:
        model = Document
        fields = (
            'id', 'uuid', 'title', 'slug', 'status',
            'client_name', 'client', 'client_display_name',
            'project', 'project_name',
            'document_type_code', 'commercial_status',
            'language', 'cover_type', 'template_style',
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


class DocumentDetailSerializer(ClientProjectReadMixin, serializers.ModelSerializer):
    """Full serializer for document detail view."""

    folder_name = serializers.CharField(source='folder.name', read_only=True, default=None)
    client = serializers.SerializerMethodField()
    client_display_name = serializers.SerializerMethodField()
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)
    # The edit page locks issued cuentas; both fields feed that branch.
    document_type_code = serializers.CharField(
        source='document_type.code', read_only=True, default=None,
    )
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
            'client_name', 'client', 'client_display_name',
            'project', 'project_name',
            'document_type_code', 'commercial_status',
            'language', 'cover_type', 'template_style',
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
    # Sin acotar por cliente a propósito: un queryset de campo no ve el valor
    # de su hermano, así que la regla de pertenencia vive en validate().
    client = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.clients(), required=False, allow_null=True,
    )
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(), required=False, allow_null=True,
    )

    class Meta:
        model = Document
        fields = (
            'title', 'client_name', 'language', 'cover_type', 'template_style',
            'include_portada', 'include_subportada', 'include_contraportada',
            'status', 'content_markdown', 'content_json',
            'folder_id', 'tag_ids', 'client', 'project',
        )
        extra_kwargs = {
            'title': {'required': True},
            'content_markdown': {'required': False},
            'content_json': {'required': False},
        }

    def validate(self, attrs):
        """Guarda de carpeta archivada + resolución de la asociación.

        Ambas van a nivel de objeto y no de campo porque dependen del estado
        de la propia instancia: mover un documento YA archivado entre carpetas
        es un caso soportado, y la pertenencia proyecto→cliente compara campos
        hermanos.
        """
        if 'folder' in attrs:
            try:
                ensure_active_target(
                    attrs['folder'],
                    moving_archived=bool(self.instance and self.instance.is_archived),
                )
            except DocumentArchiveError as exc:
                raise serializers.ValidationError({'folder_id': str(exc)}) from exc
        return apply_client_project_association(attrs, self.instance)

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
    client = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.clients(), required=False, allow_null=True,
    )
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(), required=False, allow_null=True,
    )

    def validate_folder_id(self, value):
        """Un documento nuevo nace activo: su carpeta tiene que estarlo también."""
        try:
            ensure_active_target(value)
        except DocumentArchiveError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value

    def validate(self, attrs):
        return apply_client_project_association(attrs)
