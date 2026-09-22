"""History context is reset before transaction on-commit writers run."""

import pytest
from django.db import transaction

from content.models import Document, EntityHistory
from content.services.entity_history import history_operation


@pytest.mark.django_db(transaction=True)
def test_on_commit_write_records_history_after_parent_operation_commits():
    """Fails if an on-commit document write remains attached to an already-flushed operation."""
    callback_result = {}

    def create_callback_document():
        callback_result['document'] = Document.objects.create(title='Documento post-commit')

    with history_operation():
        original = Document.objects.create(title='Documento principal')
        transaction.on_commit(create_callback_document)

    callback_document = callback_result['document']
    assert EntityHistory.objects.get(
        entity_type='document', object_id=original.pk,
    ).entries.get().snapshot['title'] == 'Documento principal'
    assert EntityHistory.objects.get(
        entity_type='document', object_id=callback_document.pk,
    ).entries.get().snapshot['title'] == 'Documento post-commit'
