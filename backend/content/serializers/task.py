from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from content.models import Task, TaskAlert, TaskComment

User = get_user_model()


class TaskListSerializer(serializers.ModelSerializer):
    """Read-only representation for Kanban columns."""

    assignee_name = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            'id', 'title', 'description',
            'status', 'priority', 'board_type',
            'assignee', 'assignee_name',
            'due_date', 'is_overdue',
            'position', 'is_archived', 'archive_reason',
            'created_at', 'updated_at',
        )

    def get_assignee_name(self, obj):
        user = obj.assignee
        if not user:
            return None
        full = (user.get_full_name() or '').strip()
        return full or user.username

    def get_is_overdue(self, obj):
        if not obj.due_date or obj.status == Task.Status.DONE:
            return False
        today = self.context.get('today') or timezone.localdate()
        return obj.due_date < today


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """Write-side serializer for create/update."""

    assignee_id = serializers.PrimaryKeyRelatedField(
        source='assignee', queryset=User.objects.all(),
        required=False, allow_null=True,
    )

    class Meta:
        model = Task
        fields = (
            'title', 'description',
            'status', 'priority', 'board_type',
            'assignee_id', 'due_date', 'position',
        )
        extra_kwargs = {
            'title': {'required': True},
            'status': {'required': False},
            'priority': {'required': False},
            'board_type': {'required': False},
        }


class TaskCommentSerializer(serializers.ModelSerializer):
    """Read-only representation of a task comment."""

    author_name = serializers.SerializerMethodField()

    class Meta:
        model = TaskComment
        fields = ('id', 'text', 'author', 'author_name', 'created_at')

    def get_author_name(self, obj):
        if not obj.author:
            return 'Unknown'
        full = (obj.author.get_full_name() or '').strip()
        return full or obj.author.username


class TaskCommentCreateSerializer(serializers.ModelSerializer):
    """Write-side serializer for creating a task comment."""

    class Meta:
        model = TaskComment
        fields = ('text',)
        extra_kwargs = {'text': {'required': True}}


class TaskAlertSerializer(serializers.ModelSerializer):
    """Read-only representation of a task alert."""

    class Meta:
        model = TaskAlert
        fields = ('id', 'notify_at', 'note', 'sent', 'created_at')


class TaskAlertCreateSerializer(serializers.ModelSerializer):
    """Write-side serializer for creating a task alert."""

    class Meta:
        model = TaskAlert
        fields = ('notify_at', 'note')
        extra_kwargs = {
            'notify_at': {'required': True},
            'note': {'required': False},
        }
