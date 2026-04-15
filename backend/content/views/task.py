from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import Task
from content.serializers.task import (
    TaskCreateUpdateSerializer,
    TaskListSerializer,
)


_STATUS_KEYS = [s.value for s in Task.Status]


def _next_position(status_value, exclude_pk=None):
    """Return the next position index at the end of the given status column."""
    queryset = Task.objects.filter(status=status_value)
    if exclude_pk is not None:
        queryset = queryset.exclude(pk=exclude_pk)
    last = queryset.aggregate(max=Max('position'))['max']
    return (last or 0) + 1


def _serializer_context():
    return {'today': timezone.localdate()}


def _grouped_tasks():
    """Return a dict keyed by status, each value is an ordered list of tasks."""
    grouped = {key: [] for key in _STATUS_KEYS}
    queryset = Task.objects.select_related('assignee').order_by('position', '-created_at')
    for task in queryset:
        grouped.setdefault(task.status, []).append(task)
    context = _serializer_context()
    return {
        key: TaskListSerializer(grouped[key], many=True, context=context).data
        for key in _STATUS_KEYS
    }


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_tasks(request):
    """Return tasks grouped by status for the Kanban board."""
    return Response(_grouped_tasks())


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_task(request):
    """Create a task. Appends to the end of its status column."""
    serializer = TaskCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    target_status = serializer.validated_data.get('status', Task.Status.TODO)
    task = serializer.save(position=_next_position(target_status))
    return Response(
        TaskListSerializer(task, context=_serializer_context()).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_task(request, task_id):
    """Update any task field, including status (moves to another column)."""
    task = get_object_or_404(Task, pk=task_id)
    serializer = TaskCreateUpdateSerializer(task, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    previous_status = task.status
    new_status = serializer.validated_data.get('status', previous_status)
    status_changed = 'status' in serializer.validated_data and new_status != previous_status
    if status_changed and 'position' not in request.data:
        serializer.validated_data['position'] = _next_position(new_status, exclude_pk=task.pk)

    task = serializer.save()
    return Response(
        TaskListSerializer(task, context=_serializer_context()).data,
    )


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def reorder_task(request, task_id):
    """Move a task to a specific (status, position) and renumber the column.

    Body: {"status": "<status>", "position": <0-based index>}
    """
    task = get_object_or_404(Task, pk=task_id)
    new_status = request.data.get('status', task.status)
    if new_status not in _STATUS_KEYS:
        return Response(
            {'status': 'Invalid status.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        new_index = int(request.data.get('position', 0))
    except (TypeError, ValueError):
        return Response(
            {'position': 'Invalid position.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if new_index < 0:
        new_index = 0

    with transaction.atomic():
        task.status = new_status
        task.save(update_fields=['status'])

        column = list(
            Task.objects.filter(status=new_status)
            .exclude(pk=task.pk)
            .order_by('position', 'created_at')
        )
        if new_index > len(column):
            new_index = len(column)
        column.insert(new_index, task)

        for index, item in enumerate(column):
            if item.position != index:
                item.position = index
                item.save(update_fields=['position'])

    return Response(_grouped_tasks())


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_task(request, task_id):
    """Remove a task."""
    task = get_object_or_404(Task, pk=task_id)
    task.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
