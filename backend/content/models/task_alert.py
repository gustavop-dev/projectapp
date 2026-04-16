from django.db import models

from .task import Task


class TaskAlert(models.Model):
    """A manually-defined email alert for a task, fired on notify_at date."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='alerts')
    notify_at = models.DateField()
    note = models.TextField(blank=True, default='')
    sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['notify_at', 'created_at']

    def __str__(self):
        return f'Alert for "{self.task.title}" on {self.notify_at}'
