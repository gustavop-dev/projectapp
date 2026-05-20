from rest_framework import serializers

from content.models import DocumentFolder


class DocumentFolderSerializer(serializers.ModelSerializer):
    """Serializer para carpetas de documentos (jerárquicas).

    `document_count` y `children_count` se leen de annotations del queryset
    cuando el caller las provee; de lo contrario caen a un COUNT por carpeta
    para que las respuestas single-object (create/update) sigan incluyendo los
    campos.
    """

    document_count = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    parent = serializers.PrimaryKeyRelatedField(
        queryset=DocumentFolder.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = DocumentFolder
        fields = (
            'id', 'name', 'slug', 'parent', 'order',
            'document_count', 'children_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('slug', 'created_at', 'updated_at')

    def get_document_count(self, obj):
        value = getattr(obj, 'document_count', None)
        if isinstance(value, int):
            return value
        return obj.documents.count()

    def get_children_count(self, obj):
        value = getattr(obj, 'children_count', None)
        if isinstance(value, int):
            return value
        return obj.children.count()

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
        return value
