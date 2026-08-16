from accounts.models import Project, UserProfile
from rest_framework import serializers

from content.models import DocumentFolder
from content.serializers.document import (
    ClientProjectReadMixin, apply_client_project_association,
)
from content.services.document_archive_service import (
    DocumentArchiveError, ensure_active_target,
)


class DocumentFolderChangeClientSerializer(serializers.Serializer):
    """Payload del apply de cambio de cliente.

    `mode` va sin default a propósito: el operador elige cada vez qué pasa con
    el contenido. Las dos listas de ids son el token de staleness — el plan que
    corre es el que se mostró en el preview, o no corre nada.
    """

    client_profile_id = serializers.IntegerField()
    mode = serializers.CharField()
    document_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list,
    )
    folder_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list,
    )


class DocumentFolderSerializer(ClientProjectReadMixin, serializers.ModelSerializer):
    """Serializer para carpetas de documentos (jerárquicas).

    Los contadores se leen de annotations del queryset cuando el caller las
    provee; de lo contrario caen a un COUNT por carpeta para que las respuestas
    single-object (create/update) sigan incluyendo los campos.

    `document_count`/`children_count` son relativos al estado de la carpeta
    (una activa cuenta contenido activo) y se conservan por compatibilidad. Los
    cuatro `active_*`/`archived_*` son absolutos: sumarlos siempre da el
    contenido real, mientras que sumar los relativos duplicaría el conteo de una
    carpeta archivada. Son además los que permiten a una carpeta activa avisar
    que todavía guarda elementos archivados.
    """

    document_count = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    active_document_count = serializers.SerializerMethodField()
    active_children_count = serializers.SerializerMethodField()
    archived_document_count = serializers.SerializerMethodField()
    archived_children_count = serializers.SerializerMethodField()
    archived_cause = serializers.SerializerMethodField()
    parent = serializers.PrimaryKeyRelatedField(
        queryset=DocumentFolder.objects.all(),
        required=False,
        allow_null=True,
    )
    # `client` habla en pk de UserProfile como todo el panel; el modelo
    # persiste `client_user` (auth.User). A diferencia de los documentos —que
    # separan serializer de lectura y de escritura— acá uno solo sirve list,
    # create y update, así que el campo se declara write_only y la lectura la
    # devuelve `to_representation` con el mismo mapeo del mixin.
    # Los dos querysets van sin acotar a propósito: que el proyecto sea del
    # cliente es cosa de validate(), que ve ambos campos a la vez (mismo
    # motivo que en DocumentCreateUpdateSerializer).
    client = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.clients(),
        required=False,
        allow_null=True,
        write_only=True,
    )
    client_display_name = serializers.SerializerMethodField()
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        required=False,
        allow_null=True,
    )
    project_name = serializers.CharField(
        source='project.name', read_only=True, default=None,
    )

    class Meta:
        model = DocumentFolder
        fields = (
            'id', 'name', 'slug', 'parent', 'order',
            'client', 'client_display_name', 'project', 'project_name',
            'document_count', 'children_count',
            'active_document_count', 'active_children_count',
            'archived_document_count', 'archived_children_count',
            'created_at', 'updated_at',
            'is_archived', 'archived_at', 'archived_cause',
        )
        # `is_archived`/`archived_at` son read-only a propósito: update_document_folder
        # usa este mismo serializer para PATCH, y dejarlos escribibles permitiría
        # archivar saltándose la cascada del servicio.
        read_only_fields = (
            'slug', 'created_at', 'updated_at', 'is_archived', 'archived_at',
        )

    def get_document_count(self, obj):
        attr = 'archived_document_count' if obj.is_archived else 'active_document_count'
        value = getattr(obj, attr, None)
        if isinstance(value, int):
            return value
        # Sin annotation (respuestas single-object) el conteo sigue el mismo
        # scope que la lista: una carpeta activa cuenta documentos activos.
        return obj.documents.filter(is_archived=obj.is_archived).count()

    def get_children_count(self, obj):
        attr = 'archived_children_count' if obj.is_archived else 'active_children_count'
        value = getattr(obj, attr, None)
        if isinstance(value, int):
            return value
        return obj.children.filter(is_archived=obj.is_archived).count()

    def get_active_document_count(self, obj):
        value = getattr(obj, 'active_document_count', None)
        if isinstance(value, int):
            return value
        return obj.documents.filter(is_archived=False).count()

    def get_active_children_count(self, obj):
        value = getattr(obj, 'active_children_count', None)
        if isinstance(value, int):
            return value
        return obj.children.filter(is_archived=False).count()

    def get_archived_document_count(self, obj):
        value = getattr(obj, 'archived_document_count', None)
        if isinstance(value, int):
            return value
        return obj.documents.filter(is_archived=True).count()

    def get_archived_children_count(self, obj):
        value = getattr(obj, 'archived_children_count', None)
        if isinstance(value, int):
            return value
        return obj.children.filter(is_archived=True).count()

    def get_archived_cause(self, obj):
        """'folder' si lo arrastró una carpeta, 'manual' si fue por sí misma."""
        if not obj.is_archived:
            return None
        return 'folder' if obj.archived_via_folder_id else 'manual'

    def to_representation(self, instance):
        """Devuelve `client` como pk de UserProfile (el campo es write_only)."""
        data = super().to_representation(instance)
        data['client'] = self.get_client(instance)
        return data

    def validate(self, attrs):
        """Misma regla de asociación que los documentos, sin `client_name`."""
        return apply_client_project_association(
            attrs, self.instance, snapshot_client_name=False,
        )

    def validate_parent(self, value):
        """Impide que una carpeta sea su propio padre o descienda de sí misma."""
        if value is None:
            return value
        instance = self.instance
        if instance is not None:
            if value.pk == instance.pk:
                raise serializers.ValidationError(
                    'Una carpeta no puede ser su propio padre.'
                )
            if value.pk in instance.get_descendant_ids():
                raise serializers.ValidationError(
                    'No se puede mover una carpeta dentro de una de sus subcarpetas.'
                )
        try:
            ensure_active_target(
                value, moving_archived=bool(instance and instance.is_archived),
            )
        except DocumentArchiveError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value
