"""Tests for the document-thread tools of the Documents MCP connector."""
import json

import pytest

from content.models import (
    Document,
    DocumentFolder,
    DocumentThread,
    DocumentThreadItem,
    DocumentType,
    McpConnector,
)


@pytest.fixture
def markdown_doc_type(db):
    obj, _ = DocumentType.objects.get_or_create(
        code='markdown',
        defaults={'name': 'Markdown', 'label': 'Markdown'},
    )
    return obj


@pytest.fixture
def collection_account_type(db):
    obj, _ = DocumentType.objects.get_or_create(
        code='collection_account',
        defaults={'name': 'Cuenta de cobro', 'label': 'Cuenta de cobro'},
    )
    return obj


@pytest.fixture
def documents_connector(db, superuser):
    connector, _ = McpConnector.objects.get_or_create(
        slug='documents', defaults={'name': 'Gestor Documental'},
    )
    connector.is_active = True
    connector.save(update_fields=['is_active'])
    return connector, connector.generate_token()


def _make_doc(doc_type, **kwargs):
    defaults = {
        'title': 'Doc',
        'document_type': doc_type,
        'language': 'es',
        'content_markdown': '# Hola\n\nMundo.',
        'content_json': {'meta': {}, 'blocks': []},
    }
    defaults.update(kwargs)
    return Document.objects.create(**defaults)


def _call(api_client, token, name, arguments):
    return api_client.post(
        f'/api/mcp/documents/{token}/',
        {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/call',
            'params': {'name': name, 'arguments': arguments},
        },
        format='json',
    )


def _call_confirmed(api_client, token, name, arguments):
    preview = _call(api_client, token, name, arguments)
    confirmation_id = preview.data['result']['structuredContent']['confirmation_id']
    return _call(
        api_client,
        token,
        'confirm_action',
        {'confirmation_id': confirmation_id},
    )


def _payload(response):
    """The tool result, decoded. Fails loudly when the tool reported an error."""
    result = response.data['result']
    text = result['content'][0]['text']
    assert result['isError'] is False, text
    payload = json.loads(text)
    return payload.get('result', payload) if payload.get('confirmed') else payload


def _error_text(response):
    result = response.data['result']
    assert result['isError'] is True, result
    return result['content'][0]['text']


@pytest.fixture
def three_documents(markdown_doc_type):
    return [
        _make_doc(markdown_doc_type, title=f'Respuesta Etapa {index}')
        for index in range(1, 4)
    ]


@pytest.mark.django_db
class TestCreateDocumentThread:
    def test_links_two_documents_in_chronological_order(
        self, api_client, documents_connector, three_documents,
    ):
        _, token = documents_connector
        first, second, _ = three_documents

        response = _call(api_client, token, 'create_document_thread', {
            'title': 'Etapa 2 · Conteo Diario',
            'items': [
                {'document_id': second.pk, 'occurred_on': '2026-08-24'},
                {'document_id': first.pk, 'occurred_on': '2026-08-16'},
            ],
        })

        payload = _payload(response)
        assert payload['title'] == 'Etapa 2 · Conteo Diario'
        assert payload['document_count'] == 2
        assert [item['document']['id'] for item in payload['items']] == [
            first.pk, second.pk,
        ]
        assert [item['occurred_on'] for item in payload['items']] == [
            '2026-08-16', '2026-08-24',
        ]

    def test_falls_back_to_the_document_date(
        self, api_client, documents_connector, three_documents,
    ):
        _, token = documents_connector
        first, second, _ = three_documents
        Document.objects.filter(pk=first.pk).update(issue_date='2026-07-22')

        response = _call(api_client, token, 'create_document_thread', {
            'items': [
                {'document_id': first.pk},
                {'document_id': second.pk, 'occurred_on': '2026-08-16'},
            ],
        })

        payload = _payload(response)
        assert payload['items'][0]['occurred_on'] == '2026-07-22'
        assert payload['title'] == first.title

    def test_rejects_a_single_document(
        self, api_client, documents_connector, three_documents,
    ):
        _, token = documents_connector

        response = _call(api_client, token, 'create_document_thread', {
            'items': [{'document_id': three_documents[0].pk}],
        })

        assert 'al menos 2 documento' in _error_text(response)
        assert not DocumentThread.objects.exists()

    def test_reports_a_document_already_owned_by_another_thread(
        self, api_client, documents_connector, three_documents,
    ):
        _, token = documents_connector
        first, second, third = three_documents
        _call(api_client, token, 'create_document_thread', {
            'title': 'Historia original',
            'items': [{'document_id': first.pk}, {'document_id': second.pk}],
        })

        response = _call(api_client, token, 'create_document_thread', {
            'title': 'Segunda historia',
            'items': [{'document_id': second.pk}, {'document_id': third.pk}],
        })

        message = _error_text(response)
        assert 'Historia original' in message
        assert 'Retira el documento de su hilo actual' in message
        assert DocumentThread.objects.count() == 1

    def test_refuses_to_link_a_collection_account(
        self, api_client, documents_connector, three_documents,
        collection_account_type,
    ):
        _, token = documents_connector
        invoice = _make_doc(collection_account_type, title='Cuenta de cobro 001')

        response = _call(api_client, token, 'create_document_thread', {
            'items': [
                {'document_id': three_documents[0].pk},
                {'document_id': invoice.pk},
            ],
        })

        assert 'markdown activo' in _error_text(response)
        assert not DocumentThread.objects.exists()

    def test_refuses_to_link_an_archived_document(
        self, api_client, documents_connector, three_documents,
    ):
        _, token = documents_connector
        Document.objects.filter(pk=three_documents[1].pk).update(is_archived=True)

        response = _call(api_client, token, 'create_document_thread', {
            'items': [
                {'document_id': three_documents[0].pk},
                {'document_id': three_documents[1].pk},
            ],
        })

        assert 'markdown activo' in _error_text(response)

    def test_rejects_an_unparseable_date(
        self, api_client, documents_connector, three_documents,
    ):
        _, token = documents_connector

        response = _call(api_client, token, 'create_document_thread', {
            'items': [
                {'document_id': three_documents[0].pk, 'occurred_on': '16/08/2026'},
                {'document_id': three_documents[1].pk},
            ],
        })

        assert 'YYYY-MM-DD' in _error_text(response)


@pytest.mark.django_db
class TestGetDocumentThread:
    def test_returns_null_for_a_standalone_document(
        self, api_client, documents_connector, three_documents,
    ):
        _, token = documents_connector

        response = _call(api_client, token, 'get_document_thread', {
            'document_id': three_documents[0].pk,
        })

        assert _payload(response) == {'thread': None}

    def test_reads_the_thread_from_any_of_its_documents(
        self, api_client, documents_connector, three_documents,
    ):
        _, token = documents_connector
        first, second, _ = three_documents
        created = _payload(_call(api_client, token, 'create_document_thread', {
            'title': 'Historia',
            'items': [{'document_id': first.pk}, {'document_id': second.pk}],
        }))

        response = _call(api_client, token, 'get_document_thread', {
            'document_id': second.pk,
        })

        thread = _payload(response)['thread']
        assert thread['id'] == created['id']
        assert thread['title'] == 'Historia'
        assert thread['document_count'] == 2

    def test_accepts_a_thread_id(
        self, api_client, documents_connector, three_documents,
    ):
        _, token = documents_connector
        created = _payload(_call(api_client, token, 'create_document_thread', {
            'title': 'Historia',
            'items': [
                {'document_id': three_documents[0].pk},
                {'document_id': three_documents[1].pk},
            ],
        }))

        response = _call(api_client, token, 'get_document_thread', {
            'thread_id': created['id'],
        })

        assert _payload(response)['thread']['title'] == 'Historia'

    def test_requires_an_anchor(self, api_client, documents_connector):
        _, token = documents_connector

        response = _call(api_client, token, 'get_document_thread', {})

        assert 'document_id' in _error_text(response)


@pytest.mark.django_db
class TestUpdateDocumentThread:
    @pytest.fixture
    def thread_id(self, api_client, documents_connector, three_documents):
        _, token = documents_connector
        payload = _payload(_call(api_client, token, 'create_document_thread', {
            'title': 'Historia',
            'items': [
                {'document_id': three_documents[0].pk, 'occurred_on': '2026-08-16'},
                {'document_id': three_documents[1].pk, 'occurred_on': '2026-08-24'},
            ],
        }))
        return payload['id']

    def test_links_a_new_document_into_the_chronology(
        self, api_client, documents_connector, three_documents, thread_id,
    ):
        _, token = documents_connector

        response = _call(api_client, token, 'update_document_thread', {
            'thread_id': thread_id,
            'link': [
                {'document_id': three_documents[2].pk, 'occurred_on': '2026-08-20'},
            ],
        })

        payload = _payload(response)
        assert [item['document']['id'] for item in payload['items']] == [
            three_documents[0].pk, three_documents[2].pk, three_documents[1].pk,
        ]

    def test_keeps_the_members_it_was_not_told_about(
        self, api_client, documents_connector, three_documents, thread_id,
    ):
        """The incremental contract: a link never replaces the existing members."""
        _, token = documents_connector

        payload = _payload(_call(api_client, token, 'update_document_thread', {
            'thread_id': thread_id,
            'link': [{'document_id': three_documents[2].pk}],
        }))

        assert payload['document_count'] == 3
        assert {item['document']['id'] for item in payload['items']} == {
            document.pk for document in three_documents
        }

    def test_unlinks_a_document_without_deleting_it(
        self, api_client, documents_connector, three_documents, thread_id,
    ):
        _, token = documents_connector
        _call(api_client, token, 'update_document_thread', {
            'thread_id': thread_id,
            'link': [{'document_id': three_documents[2].pk}],
        })

        payload = _payload(_call(api_client, token, 'update_document_thread', {
            'thread_id': thread_id,
            'unlink_document_ids': [three_documents[1].pk],
        }))

        assert payload['document_count'] == 2
        assert three_documents[1].pk not in {
            item['document']['id'] for item in payload['items']
        }
        assert Document.objects.filter(pk=three_documents[1].pk).exists()

    def test_refuses_to_leave_the_thread_with_one_member(
        self, api_client, documents_connector, three_documents, thread_id,
    ):
        _, token = documents_connector

        response = _call(api_client, token, 'update_document_thread', {
            'thread_id': thread_id,
            'unlink_document_ids': [three_documents[1].pk],
        })

        assert 'al menos dos' in _error_text(response)
        assert DocumentThreadItem.objects.filter(thread_id=thread_id).count() == 2

    def test_renames_without_touching_the_members(
        self, api_client, documents_connector, thread_id,
    ):
        _, token = documents_connector

        payload = _payload(_call(api_client, token, 'update_document_thread', {
            'thread_id': thread_id,
            'title': 'Etapa 2 · Conteo Diario',
        }))

        assert payload['title'] == 'Etapa 2 · Conteo Diario'
        assert payload['document_count'] == 2

    def test_requires_a_change(self, api_client, documents_connector, thread_id):
        _, token = documents_connector

        response = _call(api_client, token, 'update_document_thread', {
            'thread_id': thread_id,
        })

        assert 'unlink_document_ids' in _error_text(response)

    def test_reports_an_unknown_thread(self, api_client, documents_connector):
        _, token = documents_connector

        response = _call(api_client, token, 'update_document_thread', {
            'thread_id': 9999, 'title': 'Nuevo nombre',
        })

        assert 'list_document_threads' in _error_text(response)


@pytest.mark.django_db
class TestListAndDissolve:
    @pytest.fixture
    def listed_row(self, api_client, documents_connector, three_documents):
        _, token = documents_connector
        folder = DocumentFolder.objects.create(name='QA')
        Document.objects.filter(pk=three_documents[0].pk).update(folder=folder)
        _call(api_client, token, 'create_document_thread', {
            'title': 'Etapa 2',
            'items': [
                {'document_id': three_documents[0].pk, 'occurred_on': '2026-08-16'},
                {'document_id': three_documents[1].pk, 'occurred_on': '2026-08-31'},
            ],
        })
        payload = _payload(_call(api_client, token, 'list_document_threads', {}))
        assert payload['count'] == 1
        return payload['results'][0]

    def test_lists_a_thread_with_its_date_span(self, listed_row):
        assert listed_row['title'] == 'Etapa 2'
        assert listed_row['document_count'] == 2
        assert listed_row['first_occurred_on'] == '2026-08-16'
        assert listed_row['last_occurred_on'] == '2026-08-31'

    def test_listed_thread_previews_its_latest_milestone(
        self, listed_row, three_documents,
    ):
        assert listed_row['latest_item']['document_id'] == three_documents[1].pk
        assert listed_row['documents'][0]['folder_name'] == 'QA'
        assert listed_row['documents_truncated'] is False

    def test_finds_a_thread_by_the_title_of_one_of_its_documents(
        self, api_client, documents_connector, markdown_doc_type,
    ):
        _, token = documents_connector
        first = _make_doc(markdown_doc_type, title='Reporte_QA_Etapa_2')
        second = _make_doc(markdown_doc_type, title='Respuesta_Etapa_2_R4')
        _call(api_client, token, 'create_document_thread', {
            'title': 'Historia sin pistas',
            'items': [{'document_id': first.pk}, {'document_id': second.pk}],
        })

        payload = _payload(_call(api_client, token, 'list_document_threads', {
            'search': 'Respuesta_Etapa_2',
        }))

        assert [row['title'] for row in payload['results']] == ['Historia sin pistas']

    def test_rejects_an_unknown_order(self, api_client, documents_connector):
        _, token = documents_connector

        response = _call(api_client, token, 'list_document_threads', {
            'order': 'alphabetical',
        })

        assert 'milestone' in _error_text(response)

    @pytest.fixture
    def dissolvable_thread(self, api_client, documents_connector, three_documents):
        _, token = documents_connector
        return _payload(_call(api_client, token, 'create_document_thread', {
            'title': 'Historia',
            'items': [
                {'document_id': three_documents[0].pk},
                {'document_id': three_documents[1].pk},
            ],
        }))

    def test_dissolving_releases_the_documents_without_deleting_them(
        self, api_client, documents_connector, three_documents, dissolvable_thread,
    ):
        _, token = documents_connector

        _call_confirmed(api_client, token, 'dissolve_document_thread', {
            'thread_id': dissolvable_thread['id'],
        })

        assert not DocumentThread.objects.filter(
            pk=dissolvable_thread['id'],
        ).exists()
        assert Document.objects.filter(
            pk__in=[three_documents[0].pk, three_documents[1].pk],
        ).count() == 2

    def test_dissolving_returns_the_history_it_destroyed(
        self, api_client, documents_connector, three_documents, dissolvable_thread,
    ):
        """Irreversible, so the payload has to be enough to recreate the thread."""
        _, token = documents_connector

        payload = _payload(_call_confirmed(api_client, token, 'dissolve_document_thread', {
            'thread_id': dissolvable_thread['id'],
        }))

        assert payload['dissolved'] is True
        assert payload['thread']['title'] == 'Historia'
        assert set(payload['released_document_ids']) == {
            three_documents[0].pk, three_documents[1].pk,
        }

    def test_thread_writes_are_attributed_to_the_mcp_actor(
        self, api_client, documents_connector, three_documents, superuser,
    ):
        connector, token = documents_connector

        payload = _payload(_call(api_client, token, 'create_document_thread', {
            'title': 'Historia',
            'items': [
                {'document_id': three_documents[0].pk},
                {'document_id': three_documents[1].pk},
            ],
        }))

        credential = connector.credentials.select_related('actor').get(label='Default')
        assert credential.actor_id != superuser.pk
        assert credential.actor.username == 'mcp_documents'
        assert credential.actor.has_usable_password() is False
        assert payload['created_by']['id'] == credential.actor_id
        assert all(
            item['linked_by']['id'] == credential.actor_id
            for item in payload['items']
        )
