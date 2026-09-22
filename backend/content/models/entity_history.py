"""Durable history identities and append-only revisions, independent of live rows."""

import uuid

from django.db import models
from django.utils import timezone


class EntityHistory(models.Model):
    entity_type = models.CharField(max_length=32)
    object_id = models.PositiveBigIntegerField()
    object_label = models.CharField(max_length=255)
    revision = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=('entity_type', 'object_id'), name='unique_entity_history',
        )]


class RevisionQuerySet(models.QuerySet):
    def bulk_create(self, objs, batch_size=None, **kwargs):
        if kwargs.get('update_conflicts') or kwargs.get('ignore_conflicts'):
            raise ValueError('Historical revisions cannot be overwritten.')
        return super().bulk_create(objs, batch_size=batch_size, **kwargs)

    def update(self, **kwargs):
        raise ValueError('Historical revisions cannot be edited.')

    def delete(self):
        raise ValueError('Historical revisions cannot be deleted.')


class EntityRevision(models.Model):
    objects = RevisionQuerySet.as_manager()

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError('Historical revisions cannot be edited.')
        # A newly constructed instance with an existing PK must not become UPDATE.
        kwargs['force_insert'] = True
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('Historical revisions cannot be deleted.')

    history = models.ForeignKey(EntityHistory, on_delete=models.PROTECT, related_name='entries')
    number = models.PositiveIntegerField(null=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    operation_id = models.UUIDField(default=uuid.uuid4)
    action = models.CharField(max_length=32)
    actor_id_snapshot = models.PositiveBigIntegerField(null=True)
    actor_label = models.CharField(max_length=255, default='Sistema')
    source = models.CharField(max_length=255, default='system')
    source_key = models.CharField(max_length=160, unique=True, null=True)
    # Legacy events have no complete snapshot and cannot be compared.
    snapshot = models.JSONField(null=True)
    secrets = models.JSONField(default=dict)
    changes = models.JSONField(default=list)
    changed_fields = models.JSONField(default=list)
    evidence = models.JSONField(default=list)

    class Meta:
        ordering = ('-occurred_at', '-id')
        constraints = [models.UniqueConstraint(
            fields=('history', 'number'), name='unique_entity_revision',
        )]
        indexes = [models.Index(
            fields=('history', '-occurred_at', '-id'), name='entity_revision_chronology',
        )]
