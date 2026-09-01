from datetime import date, datetime, timezone as datetime_timezone

import pytest
from django.db.models.deletion import ProtectedError

from content.models import Document, DocumentFolder, DocumentThread, DocumentThreadItem
from content.services.document_thread_service import (
    DocumentThreadError,
    create_document_thread,
    default_occurred_on,
    dissolve_document_thread,
    edit_document_thread_members,
    update_document_thread,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def documents():
    return [
        Document.objects.create(title=f'Documento {index}')
        for index in range(1, 5)
    ]


def item(document, occurred_on=None):
    payload = {'document_id': document.pk}
    if occurred_on is not None:
        payload['occurred_on'] = occurred_on
    return payload


def test_default_date_prefers_issue_date(documents):
    documents[0].issue_date = date(2026, 8, 15)
    documents[0].save(update_fields=['issue_date'])

    assert default_occurred_on(documents[0]) == date(2026, 8, 15)


def test_default_date_uses_bogota_creation_day(documents):
    Document.objects.filter(pk=documents[0].pk).update(
        created_at=datetime(2026, 9, 1, 2, 0, tzinfo=datetime_timezone.utc),
    )
    documents[0].refresh_from_db()

    assert default_occurred_on(documents[0]) == date(2026, 8, 31)


def test_create_uses_source_title_and_records_actor(documents, admin_user):
    thread = create_document_thread(
        title='',
        items=[item(documents[0]), item(documents[1])],
        actor=admin_user,
    )

    assert thread.title == 'Documento 1'
    assert thread.created_by == admin_user
    assert list(thread.items.values_list('linked_by_id', flat=True)) == [
        admin_user.pk, admin_user.pk,
    ]


def test_create_rejects_a_single_document(documents, admin_user):
    with pytest.raises(DocumentThreadError) as exc_info:
        create_document_thread(
            title='Hilo incompleto',
            items=[item(documents[0])],
            actor=admin_user,
        )

    assert exc_info.value.code == 'document_thread_requires_two_documents'
    assert not DocumentThread.objects.exists()


def test_create_rejects_a_document_from_another_thread(documents, admin_user):
    create_document_thread(
        title='Hilo original',
        items=[item(documents[0]), item(documents[1])],
        actor=admin_user,
    )

    with pytest.raises(DocumentThreadError) as exc_info:
        create_document_thread(
            title='Segundo hilo',
            items=[item(documents[1]), item(documents[2])],
            actor=admin_user,
        )

    assert exc_info.value.code == 'document_already_threaded'
    assert exc_info.value.status_code == 409


def test_update_replaces_members_atomically(documents, admin_user):
    thread = create_document_thread(
        title='Historia',
        items=[item(documents[0]), item(documents[1])],
        actor=admin_user,
    )

    updated, dissolved = update_document_thread(
        thread=thread,
        actor=admin_user,
        items=[
            item(documents[1], date(2026, 7, 1)),
            item(documents[2], date(2026, 8, 1)),
        ],
    )

    assert dissolved is False
    assert updated.pk == thread.pk
    assert list(updated.items.values_list('document_id', 'occurred_on', 'position')) == [
        (documents[1].pk, date(2026, 7, 1), 0),
        (documents[2].pk, date(2026, 8, 1), 1),
    ]
    assert not DocumentThreadItem.objects.filter(document=documents[0]).exists()


def test_update_dissolves_when_one_document_remains(documents, admin_user):
    thread = create_document_thread(
        title='Historia',
        items=[item(documents[0]), item(documents[1])],
        actor=admin_user,
    )

    updated, dissolved = update_document_thread(
        thread=thread,
        actor=admin_user,
        items=[item(documents[0])],
    )

    assert updated is None
    assert dissolved is True
    assert not DocumentThread.objects.filter(pk=thread.pk).exists()
    assert Document.objects.filter(pk__in=[documents[0].pk, documents[1].pk]).count() == 2


def test_membership_protects_the_document_until_dissolved(documents, admin_user):
    thread = create_document_thread(
        title='Historia',
        items=[item(documents[0]), item(documents[1])],
        actor=admin_user,
    )

    with pytest.raises(ProtectedError):
        documents[0].delete()

    dissolve_document_thread(thread=thread)
    documents[0].delete()
    assert not Document.objects.filter(pk=documents[0].pk).exists()


def test_thread_members_can_live_in_different_folders(documents, admin_user):
    first = DocumentFolder.objects.create(name='Contratos')
    second = DocumentFolder.objects.create(name='Entregas')
    documents[0].folder = first
    documents[0].save(update_fields=['folder'])
    documents[1].folder = second
    documents[1].save(update_fields=['folder'])

    thread = create_document_thread(
        title='Historia transversal',
        items=[item(documents[0]), item(documents[1])],
        actor=admin_user,
    )

    assert set(thread.items.values_list('document__folder_id', flat=True)) == {
        first.pk, second.pk,
    }


# ── edit_document_thread_members ─────────────────────────────────────────────

@pytest.fixture
def thread_of_two(documents, admin_user):
    return create_document_thread(
        title='Historia',
        items=[
            item(documents[0], date(2026, 8, 10)),
            item(documents[1], date(2026, 8, 20)),
        ],
        actor=admin_user,
    )


def test_edit_members_links_a_document_keeping_the_others_untouched(
    documents, admin_user, thread_of_two,
):
    before = dict(thread_of_two.items.values_list('document_id', 'id'))

    updated, dissolved = edit_document_thread_members(
        thread=thread_of_two,
        actor=admin_user,
        link=[{'document_id': documents[2].pk, 'occurred_on': date(2026, 8, 15)}],
    )

    assert dissolved is False
    assert list(
        updated.items.order_by('occurred_on', 'position', 'id')
        .values_list('document_id', flat=True)
    ) == [documents[0].pk, documents[2].pk, documents[1].pk]
    after = dict(updated.items.values_list('document_id', 'id'))
    assert after[documents[0].pk] == before[documents[0].pk]
    assert after[documents[1].pk] == before[documents[1].pk]


def test_edit_members_unlinks_a_document_without_deleting_it(
    documents, admin_user, thread_of_two,
):
    edit_document_thread_members(
        thread=thread_of_two,
        actor=admin_user,
        link=[{'document_id': documents[2].pk}],
    )

    updated, dissolved = edit_document_thread_members(
        thread=thread_of_two,
        actor=admin_user,
        unlink=[documents[1].pk],
    )

    assert dissolved is False
    assert set(updated.items.values_list('document_id', flat=True)) == {
        documents[0].pk, documents[2].pk,
    }
    assert Document.objects.filter(pk=documents[1].pk).exists()


def test_edit_members_refuses_to_leave_a_single_document(
    documents, admin_user, thread_of_two,
):
    with pytest.raises(DocumentThreadError) as excinfo:
        edit_document_thread_members(
            thread=thread_of_two,
            actor=admin_user,
            unlink=[documents[1].pk],
        )

    assert excinfo.value.code == 'document_thread_requires_two_documents'
    assert DocumentThread.objects.filter(pk=thread_of_two.pk).exists()
    assert thread_of_two.items.count() == 2


def test_edit_members_redates_a_member_and_reorders_the_chronology(
    documents, admin_user, thread_of_two,
):
    updated, _ = edit_document_thread_members(
        thread=thread_of_two,
        actor=admin_user,
        link=[{'document_id': documents[1].pk, 'occurred_on': date(2026, 8, 1)}],
    )

    assert list(
        updated.items.order_by('occurred_on', 'position', 'id')
        .values_list('document_id', 'occurred_on')
    ) == [
        (documents[1].pk, date(2026, 8, 1)),
        (documents[0].pk, date(2026, 8, 10)),
    ]


def test_edit_members_rejects_a_document_owned_by_another_thread(
    documents, admin_user, thread_of_two,
):
    create_document_thread(
        title='Otra historia',
        items=[item(documents[2]), item(documents[3])],
        actor=admin_user,
    )

    with pytest.raises(DocumentThreadError) as excinfo:
        edit_document_thread_members(
            thread=thread_of_two,
            actor=admin_user,
            link=[{'document_id': documents[2].pk}],
        )

    assert excinfo.value.code == 'document_already_threaded'
    assert excinfo.value.status_code == 409


def test_edit_members_rejects_unlinking_a_document_that_is_not_a_member(
    documents, admin_user, thread_of_two,
):
    with pytest.raises(DocumentThreadError) as excinfo:
        edit_document_thread_members(
            thread=thread_of_two,
            actor=admin_user,
            unlink=[documents[3].pk],
        )

    assert excinfo.value.code == 'document_not_in_thread'
    assert excinfo.value.status_code == 404


def test_edit_members_requires_at_least_one_change(admin_user, thread_of_two):
    with pytest.raises(DocumentThreadError) as excinfo:
        edit_document_thread_members(thread=thread_of_two, actor=admin_user)

    assert excinfo.value.code == 'document_thread_no_changes'


def test_edit_members_rejects_a_contradictory_change(
    documents, admin_user, thread_of_two,
):
    with pytest.raises(DocumentThreadError) as excinfo:
        edit_document_thread_members(
            thread=thread_of_two,
            actor=admin_user,
            link=[{'document_id': documents[1].pk}],
            unlink=[documents[1].pk],
        )

    assert excinfo.value.code == 'contradictory_thread_change'
