"""Durable-history initialization keeps legacy evidence honest and resumable."""

from django.core.management import call_command
from freezegun import freeze_time
import pytest

from content.models import AccountingChangeLog, Document, EntityHistory
from content.services.entity_history import without_history


pytestmark = pytest.mark.django_db


@freeze_time('2026-09-01 10:30:00')
def test_initialize_imports_legacy_event_once_then_adds_current_baseline():
    """Fails if rerunning initialization duplicates evidence or invents an old snapshot."""
    with without_history():
        document = Document.objects.create(title='Contrato existente', content_markdown='Actual')
    legacy = AccountingChangeLog.objects.create(
        entity_type=AccountingChangeLog.EntityType.DOCUMENT,
        object_id=document.pk,
        object_repr='Contrato existente',
        action=AccountingChangeLog.Action.UPDATED,
        changes=[{'field': 'title', 'label': 'Título', 'old': 'Antes', 'new': 'Actual'}],
        actor_username='editora',
    )

    with freeze_time('2026-09-20 10:30:00'):
        call_command('initialize_entity_history', entity_type='document', batch_size=1)
        first_count = EntityHistory.objects.get(
            entity_type='document', object_id=document.pk,
        ).entries.count()
        call_command('initialize_entity_history', entity_type='document', batch_size=1)

    head = EntityHistory.objects.get(entity_type='document', object_id=document.pk)
    legacy_revision = head.entries.get(source_key=f'accounting:{legacy.pk}')
    baseline = head.entries.get(action='baseline')
    assert head.entries.count() == first_count
    assert head.entries.filter(source_key=f'accounting:{legacy.pk}').count() == 1
    assert head.entries.filter(action='baseline').count() == 1
    assert legacy_revision.snapshot is None
    assert legacy_revision.occurred_at == legacy.created_at
    assert legacy_revision.actor_label == 'editora'
    assert baseline.snapshot['content_markdown'] == 'Actual'
