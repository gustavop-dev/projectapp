from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from content.models import Task, TaskAlert, TaskComment
from content.serializers.task import (
    TaskAlertCreateSerializer,
    TaskAlertSerializer,
    TaskCommentCreateSerializer,
    TaskCommentSerializer,
    TaskCreateUpdateSerializer,
    TaskListSerializer,
)

User = get_user_model()


_STATUS_KEYS = [s.value for s in Task.Status]
_BOARD_KEYS = [b.value for b in Task.BoardType]


def _next_position(status_value, board_type=Task.BoardType.STANDARD, exclude_pk=None):
    """Return the next position index at the end of the given status+board column."""
    queryset = Task.objects.filter(status=status_value, board_type=board_type)
    if exclude_pk is not None:
        queryset = queryset.exclude(pk=exclude_pk)
    last = queryset.aggregate(max=Max('position'))['max']
    return (last or 0) + 1


def _serializer_context():
    return {'today': timezone.localdate()}


def _grouped_board_tasks(board_type):
    """Return active (non-archived) tasks for a specific board, grouped by status."""
    context = _serializer_context()
    if board_type == Task.BoardType.MACRO:
        tasks = Task.objects.filter(
            board_type=board_type, is_archived=False,
        ).select_related('assignee').order_by('position', '-created_at')
        return {'items': TaskListSerializer(tasks, many=True, context=context).data}

    grouped = {key: [] for key in _STATUS_KEYS}
    queryset = Task.objects.filter(
        board_type=board_type, is_archived=False,
    ).select_related('assignee').order_by('position', '-created_at')
    for task in queryset:
        grouped.setdefault(task.status, []).append(task)
    return {
        key: TaskListSerializer(grouped[key], many=True, context=context).data
        for key in _STATUS_KEYS
    }


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_tasks(request):
    """Return tasks grouped by status for a specific board.

    Query param: ?board=standard|weekly|monthly|macro (default: standard)
    """
    board = request.query_params.get('board', Task.BoardType.STANDARD)
    if board not in _BOARD_KEYS:
        return Response({'board': 'Invalid board type.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(_grouped_board_tasks(board))


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_task(request):
    """Create a task. Appends to the end of its status column within the same board."""
    serializer = TaskCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    target_status = serializer.validated_data.get('status', Task.Status.TODO)
    target_board = serializer.validated_data.get('board_type', Task.BoardType.STANDARD)
    task = serializer.save(position=_next_position(target_status, board_type=target_board))
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
    current_board = task.board_type
    status_changed = 'status' in serializer.validated_data and new_status != previous_status
    if status_changed and 'position' not in request.data:
        serializer.validated_data['position'] = _next_position(
            new_status, board_type=current_board, exclude_pk=task.pk,
        )

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
            Task.objects.filter(status=new_status, board_type=task.board_type)
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

    return Response(_grouped_board_tasks(task.board_type))


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_task(request, task_id):
    """Remove a task."""
    task = get_object_or_404(Task, pk=task_id)
    task.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_task_assignees(request):
    """Return all active staff users as assignee options for the task form dropdown."""
    users = User.objects.filter(is_staff=True, is_active=True).order_by('first_name', 'username')
    data = [
        {'id': u.id, 'name': (u.get_full_name().strip() or u.username)}
        for u in users
    ]
    return Response(data)


# ── Archive / Unarchive ──────────────────────────────────────────────────────

@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def archive_task(request, task_id):
    """Archive a task, optionally recording a reason."""
    task = get_object_or_404(Task, pk=task_id)
    task.is_archived = True
    task.archive_reason = (request.data.get('archive_reason') or '').strip()
    task.save(update_fields=['is_archived', 'archive_reason'])
    return Response(TaskListSerializer(task, context=_serializer_context()).data)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def unarchive_task(request, task_id):
    """Restore an archived task to its board."""
    task = get_object_or_404(Task, pk=task_id)
    task.is_archived = False
    task.archive_reason = ''
    task.save(update_fields=['is_archived', 'archive_reason'])
    return Response(TaskListSerializer(task, context=_serializer_context()).data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_archived_tasks(request):
    """Return all archived tasks across all boards."""
    tasks = Task.objects.filter(is_archived=True).select_related('assignee').order_by('-updated_at')
    return Response(TaskListSerializer(tasks, many=True, context=_serializer_context()).data)


# ── Task Comments ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_task_comments(request, task_id):
    """Return all comments for a task, ordered by creation date."""
    task = get_object_or_404(Task, pk=task_id)
    comments = task.comments.select_related('author').all()
    return Response(TaskCommentSerializer(comments, many=True).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_task_comment(request, task_id):
    """Add a comment to a task. Author is set to the requesting user."""
    task = get_object_or_404(Task, pk=task_id)
    serializer = TaskCommentCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    comment = serializer.save(task=task, author=request.user)
    return Response(TaskCommentSerializer(comment).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_task_comment(request, task_id, comment_id):
    """Delete a comment from a task."""
    comment = get_object_or_404(TaskComment, pk=comment_id, task_id=task_id)
    comment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Task Alerts ──────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_task_alerts(request, task_id):
    """Return all alerts for a task, ordered by notify_at."""
    task = get_object_or_404(Task, pk=task_id)
    alerts = task.alerts.all()
    return Response(TaskAlertSerializer(alerts, many=True).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_task_alert(request, task_id):
    """Create a manual alert for a task."""
    task = get_object_or_404(Task, pk=task_id)
    serializer = TaskAlertCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    alert = serializer.save(task=task)
    return Response(TaskAlertSerializer(alert).data, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_task_alert(request, task_id, alert_id):
    """Delete a manual alert."""
    alert = get_object_or_404(TaskAlert, pk=alert_id, task_id=task_id)
    alert.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
