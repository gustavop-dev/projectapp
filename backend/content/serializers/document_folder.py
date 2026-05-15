from rest_framework import serializers

from content.models import DocumentFolder


class DocumentFolderSerializer(serializers.ModelSerializer):
    """Serializer for hierarchical document folders.

    `document_count` is recursive: it includes documents directly in the folder
    plus documents in every descendant. Callers may pre-compute the tree and
    pass `children_map` + `direct_counts` via serializer context to avoid N+1
    queries; otherwise the serializer falls back to per-folder queries.

    `path` is read-only and lists ancestors root→self (inclusive of self).
    `depth` is the integer depth (0 for root).
    """

    parent = serializers.PrimaryKeyRelatedField(
        queryset=DocumentFolder.objects.all(),
        allow_null=True,
        required=False,
    )
    document_count = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()
    depth = serializers.SerializerMethodField()

    class Meta:
        model = DocumentFolder
        fields = (
            'id', 'name', 'slug', 'order', 'parent',
            'document_count', 'path', 'depth',
            'created_at', 'updated_at',
        )
        read_only_fields = ('slug', 'created_at', 'updated_at')

    def get_document_count(self, obj):
        recursive_counts = self.context.get('recursive_counts')
        if recursive_counts and obj.pk in recursive_counts:
            return recursive_counts[obj.pk]
        direct_counts = self.context.get('direct_counts')
        children_map = self.context.get('children_map')
        if direct_counts is not None and children_map is not None:
            total = direct_counts.get(obj.pk, 0)
            stack = list(children_map.get(obj.pk, []))
            while stack:
                child = stack.pop()
                total += direct_counts.get(child.pk, 0)
                stack.extend(children_map.get(child.pk, []))
            return total
        # Fallback for create/update single-object responses.
        descendant_ids = obj.get_descendant_ids(include_self=True)
        from content.models import Document  # avoid circular import at module load
        return Document.objects.filter(folder_id__in=descendant_ids).count()

    def get_path(self, obj):
        folder_by_id = self.context.get('folder_by_id')
        chain = []
        if folder_by_id:
            current = obj
            seen = set()
            while current is not None:
                if current.pk in seen:
                    break
                seen.add(current.pk)
                chain.append({'id': current.pk, 'name': current.name})
                current = folder_by_id.get(current.parent_id) if current.parent_id else None
        else:
            for ancestor in obj.get_ancestors():
                chain.append({'id': ancestor.pk, 'name': ancestor.name})
            chain.append({'id': obj.pk, 'name': obj.name})
            return chain
        chain.reverse()
        return chain

    def get_depth(self, obj):
        folder_by_id = self.context.get('folder_by_id')
        if folder_by_id:
            depth = 0
            seen = set()
            parent_id = obj.parent_id
            while parent_id is not None and parent_id not in seen:
                seen.add(parent_id)
                depth += 1
                parent = folder_by_id.get(parent_id)
                parent_id = parent.parent_id if parent else None
            return depth
        return obj.get_depth()

    def validate(self, attrs):
        parent = attrs.get('parent', self.instance.parent if self.instance else None)
        instance = self.instance
        if parent is not None:
            # self-parent
            if instance and parent.pk == instance.pk:
                raise serializers.ValidationError(
                    {'parent': 'Una carpeta no puede ser su propio padre.'}
                )
            # cycle
            if instance:
                descendants = instance.get_descendant_ids(include_self=False)
                if parent.pk in descendants:
                    raise serializers.ValidationError(
                        {'parent': 'No se puede mover una carpeta dentro de sus descendientes.'}
                    )
            # depth
            from content.models.document_folder import MAX_FOLDER_DEPTH
            parent_depth = parent.get_depth()
            if parent_depth + 1 >= MAX_FOLDER_DEPTH:
                raise serializers.ValidationError(
                    {'parent': f'Profundidad máxima de {MAX_FOLDER_DEPTH} niveles excedida.'}
                )
        return attrs
