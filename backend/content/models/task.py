from django.conf import settings
from django.db import models


class Task(models.Model):
    """Kanban task managed from the admin panel."""

    class Status(models.TextChoices):
        TODO = 'todo', 'TO DO'
        IN_PROGRESS = 'in_progress', 'In Progress'
        BLOCKED = 'blocked', 'Blocked'
        DONE = 'done', 'Done'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20, choices=Status.choices,
        default=Status.TODO, db_index=True,
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='assigned_tasks',
    )
    due_date = models.DateField(null=True, blank=True)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Deadline notification tracking — set by check_task_deadline_notifications()
    notified_40 = models.BooleanField(default=False)
    notified_70 = models.BooleanField(default=False)
    notified_100 = models.BooleanField(default=False)
    last_overdue_notified_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['status', 'position', '-created_at']

    def __str__(self):
        return self.title
