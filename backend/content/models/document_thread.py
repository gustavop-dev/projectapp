from django.conf import settings
from django.db import models


class DocumentThread(models.Model):
    """An ordered, folder-independent history shared by related documents."""

    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='document_threads_created',
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='document_threads_updated',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-id']

    def __str__(self):
        return self.title


class DocumentThreadItem(models.Model):
    """One document in a thread, dated by the business chronology."""

    thread = models.ForeignKey(
        DocumentThread,
        on_delete=models.CASCADE,
        related_name='items',
    )
    document = models.OneToOneField(
        'content.Document',
        on_delete=models.PROTECT,
        related_name='thread_item',
    )
    occurred_on = models.DateField(db_index=True)
    position = models.PositiveIntegerField(default=0)
    linked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='document_thread_items_linked',
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='document_thread_items_updated',
        null=True,
        blank=True,
    )
    linked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['occurred_on', 'position', 'id']
        indexes = [
            models.Index(
                fields=['thread', 'occurred_on', 'position'],
                name='docthreaditem_chronology',
            ),
        ]

    def __str__(self):
        return f'{self.thread}: {self.document}'
