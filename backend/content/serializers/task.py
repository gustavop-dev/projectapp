from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from content.models import Task, TaskAlert

User = get_user_model()


class TaskListSerializer(serializers.ModelSerializer):
    """Read-only representation for Kanban columns."""

    assignee_name = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            'id', 'title', 'description',
            'status', 'priority',
            'assignee', 'assignee_name',
            'due_date', 'is_overdue',
            'position', 'created_at', 'updated_at',
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
            'status', 'priority',
            'assignee_id', 'due_date', 'position',
        )
        extra_kwargs = {
            'title': {'required': True},
            'status': {'required': False},
            'priority': {'required': False},
        }


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
