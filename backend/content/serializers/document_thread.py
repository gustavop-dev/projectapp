from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from content.models import Document, DocumentThread, DocumentThreadItem
from content.services.document_thread_service import default_occurred_on


def _actor_payload(actor):
    if actor is None:
        return None
    name = actor.get_full_name().strip() or actor.get_username()
    return {'id': actor.pk, 'name': name}


def _client_payload(document):
    if not document.client_user_id:
        if document.client_name:
            return {'id': None, 'name': document.client_name}
        return None
    profile = getattr(document.client_user, 'profile', None)
    if profile is None:
        return {'id': None, 'name': document.client_name or document.client_user.get_username()}
    from accounts.services.proposal_client_service import build_client_display_name
    return {'id': profile.pk, 'name': build_client_display_name(profile)}


class DocumentThreadDocumentSerializer(serializers.ModelSerializer):
    folder = serializers.SerializerMethodField()
    client = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()
    document_type_code = serializers.CharField(
        source='document_type.code', read_only=True, default=None,
    )
    is_generated_snapshot = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'id', 'title', 'slug', 'status', 'document_type_code',
            'is_generated_snapshot', 'issue_date', 'created_at',
            'is_archived', 'archived_at', 'folder', 'client', 'project',
        )

    def get_folder(self, obj):
        if not obj.folder_id:
            return None
        return {'id': obj.folder_id, 'name': obj.folder.name}

    def get_client(self, obj):
        return _client_payload(obj)

    def get_project(self, obj):
        if not obj.project_id:
            return None
        return {'id': obj.project_id, 'name': obj.project.name}

    def get_is_generated_snapshot(self, obj):
        return obj.is_generated_snapshot


class DocumentThreadItemSerializer(serializers.ModelSerializer):
    document = DocumentThreadDocumentSerializer(read_only=True)
    linked_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = DocumentThreadItem
        fields = (
            'id', 'document', 'occurred_on', 'position',
            'linked_by', 'updated_by', 'linked_at', 'updated_at',
        )

    def get_linked_by(self, obj):
        return _actor_payload(obj.linked_by)

    def get_updated_by(self, obj):
        return _actor_payload(obj.updated_by)


class DocumentThreadSerializer(serializers.ModelSerializer):
    items = DocumentThreadItemSerializer(many=True, read_only=True)
    document_count = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = DocumentThread
        fields = (
            'id', 'title', 'document_count', 'items',
            'created_by', 'updated_by', 'created_at', 'updated_at',
        )

    def get_document_count(self, obj):
        value = getattr(obj, 'document_count', None)
        return value if value is not None else len(obj.items.all())

    def get_created_by(self, obj):
        return _actor_payload(obj.created_by)

    def get_updated_by(self, obj):
        return _actor_payload(obj.updated_by)


class DocumentThreadCandidateSerializer(DocumentThreadDocumentSerializer):
    default_occurred_on = serializers.SerializerMethodField()
    available = serializers.SerializerMethodField()
    unavailable_reason = serializers.SerializerMethodField()
    thread_summary = serializers.SerializerMethodField()

    class Meta(DocumentThreadDocumentSerializer.Meta):
        fields = DocumentThreadDocumentSerializer.Meta.fields + (
            'default_occurred_on', 'available', 'unavailable_reason',
            'thread_summary',
        )

    @staticmethod
    def _membership(obj):
        try:
            return obj.thread_item
        except (AttributeError, ObjectDoesNotExist):
            return None

    def get_default_occurred_on(self, obj):
        return default_occurred_on(obj)

    def get_available(self, obj):
        return self._membership(obj) is None

    def get_unavailable_reason(self, obj):
        membership = self._membership(obj)
        if membership is None:
            return None
        return f'Ya pertenece al hilo “{membership.thread.title}”.'

    def get_thread_summary(self, obj):
        membership = self._membership(obj)
        if membership is None:
            return None
        count = getattr(obj, 'thread_document_count', None)
        if count is None:
            count = membership.thread.items.count()
        return {
            'id': membership.thread_id,
            'title': membership.thread.title,
            'document_count': count,
        }


class DocumentThreadItemInputSerializer(serializers.Serializer):
    document_id = serializers.IntegerField(min_value=1)
    occurred_on = serializers.DateField(required=False, allow_null=True)


class DocumentThreadCreateSerializer(serializers.Serializer):
    title = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default='',
    )
    items = DocumentThreadItemInputSerializer(many=True, min_length=2)


class DocumentThreadUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False, allow_blank=False)
    items = DocumentThreadItemInputSerializer(
        many=True, required=False, min_length=1,
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                'Envía el nombre o los documentos que deseas actualizar.',
            )
        return attrs
