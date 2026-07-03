"""Tests for the Documents MCP connector HTTP endpoint."""
import pytest

from content.models import Document, DocumentFolder, DocumentType, McpConnector


@pytest.fixture
def markdown_doc_type(db):
    """Reuse or create the 'markdown' DocumentType (seeded by migration 0052)."""
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
def documents_connector(db):
    connector, _ = McpConnector.objects.get_or_create(
        slug='documents', defaults={'name': 'Gestor de Documentos'},
    )
    connector.is_active = True
    connector.save(update_fields=['is_active'])
    token = connector.generate_token()
    return connector, token


def _url(token):
    return f'/api/mcp/documents/{token}/'


def _rpc(method, params=None, msg_id=1):
    message = {'jsonrpc': '2.0', 'id': msg_id, 'method': method}
    if params is not None:
        message['params'] = params
    return message


def _call(api_client, token, name, arguments):
    return api_client.post(
        _url(token),
        _rpc('tools/call', {'name': name, 'arguments': arguments}),
        format='json',
    )


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


@pytest.mark.django_db
class TestDocumentsMcpToolList:
    def test_exposes_the_seven_tools(self, api_client, documents_connector):
        _, token = documents_connector
        response = api_client.post(_url(token), _rpc('tools/list'), format='json')
        names = [t['name'] for t in response.data['result']['tools']]
        assert names == [
            'list_folders', 'create_folder', 'list_documents',
            'read_document', 'create_document', 'update_document',
            'delete_document',
        ]

    def test_serverinfo_handshake_works_on_shared_endpoint(self, api_client, documents_connector):
        _, token = documents_connector
        response = api_client.post(
            _url(token), _rpc('initialize', {'protocolVersion': '2025-06-18'}),
            format='json',
        )
        assert response.status_code == 200
        assert response.data['result']['capabilities']['tools'] == {}


@pytest.mark.django_db
class TestDocumentsMcpFolders:
    def test_list_folders_returns_path_and_counts(self, api_client, documents_connector, markdown_doc_type):
        parent = DocumentFolder.objects.create(name='Clientes')
        child = DocumentFolder.objects.create(name='ACME', parent=parent)
        _make_doc(markdown_doc_type, folder=child)
        _, token = documents_connector

        response = _call(api_client, token, 'list_folders', {})
        folders = response.data['result']['content'][0]['text']
        assert 'Clientes / ACME' in folders

    def test_create_folder_under_parent(self, api_client, documents_connector):
        parent = DocumentFolder.objects.create(name='Raíz')
        _, token = documents_connector
        response = _call(api_client, token, 'create_folder', {'name': 'Sub', 'parent_id': parent.id})
        assert response.data['result']['isError'] is False
        created = DocumentFolder.objects.get(name='Sub')
        assert created.parent_id == parent.id

    def test_create_folder_requires_name(self, api_client, documents_connector):
        _, token = documents_connector
        response = _call(api_client, token, 'create_folder', {'name': '   '})
        assert response.data['result']['isError'] is True


@pytest.mark.django_db
class TestDocumentsMcpCrud:
    def test_create_document_parses_markdown_and_builds_json(self, api_client, documents_connector, markdown_doc_type):
        _, token = documents_connector
        response = _call(api_client, token, 'create_document', {
            'title': 'Guía',
            'markdown': '# Título\n\nUn párrafo.',
        })
        assert response.data['result']['isError'] is False
        doc = Document.objects.get(title='Guía')
        assert doc.document_type.code == 'markdown'
        assert doc.content_json['blocks']  # parser produced blocks
        assert doc.content_json['meta']['title'] == 'Guía'

    def test_read_document_returns_markdown(self, api_client, documents_connector, markdown_doc_type):
        doc = _make_doc(markdown_doc_type, title='Leer', content_markdown='# X\n\nY.')
        _, token = documents_connector
        response = _call(api_client, token, 'read_document', {'document_id': doc.id})
        text = response.data['result']['content'][0]['text']
        assert '# X' in text

    def test_update_document_reparses_markdown(self, api_client, documents_connector, markdown_doc_type):
        doc = _make_doc(markdown_doc_type, title='Old')
        _, token = documents_connector
        response = _call(api_client, token, 'update_document', {
            'document_id': doc.id,
            'title': 'New',
            'markdown': '# Nuevo\n\nContenido.',
        })
        assert response.data['result']['isError'] is False
        doc.refresh_from_db()
        assert doc.title == 'New'
        assert doc.content_json['meta']['title'] == 'New'
        assert doc.content_markdown.startswith('# Nuevo')

    def test_update_document_requires_at_least_one_field(self, api_client, documents_connector, markdown_doc_type):
        doc = _make_doc(markdown_doc_type)
        _, token = documents_connector
        response = _call(api_client, token, 'update_document', {'document_id': doc.id})
        assert response.data['result']['isError'] is True

    def test_delete_unpublished_document(self, api_client, documents_connector, markdown_doc_type):
        doc = _make_doc(markdown_doc_type, status='draft')
        _, token = documents_connector
        response = _call(api_client, token, 'delete_document', {'document_id': doc.id})
        assert response.data['result']['isError'] is False
        assert not Document.objects.filter(pk=doc.id).exists()

    def test_cannot_delete_published_document(self, api_client, documents_connector, markdown_doc_type):
        doc = _make_doc(markdown_doc_type, status='published')
        _, token = documents_connector
        response = _call(api_client, token, 'delete_document', {'document_id': doc.id})
        assert response.data['result']['isError'] is True
        assert Document.objects.filter(pk=doc.id).exists()


@pytest.mark.django_db
class TestDocumentsMcpMarkdownGuardrail:
    def test_list_documents_excludes_collection_accounts(self, api_client, documents_connector, markdown_doc_type, collection_account_type):
        _make_doc(markdown_doc_type, title='Markdown doc')
        _make_doc(collection_account_type, title='Cuenta de cobro')
        _, token = documents_connector
        response = _call(api_client, token, 'list_documents', {})
        text = response.data['result']['content'][0]['text']
        assert 'Markdown doc' in text
        assert 'Cuenta de cobro' not in text

    def test_cannot_read_collection_account(self, api_client, documents_connector, collection_account_type):
        doc = _make_doc(collection_account_type, title='Cuenta')
        _, token = documents_connector
        response = _call(api_client, token, 'read_document', {'document_id': doc.id})
        assert response.data['result']['isError'] is True

    def test_cannot_delete_collection_account(self, api_client, documents_connector, collection_account_type):
        doc = _make_doc(collection_account_type, title='Cuenta', status='draft')
        _, token = documents_connector
        response = _call(api_client, token, 'delete_document', {'document_id': doc.id})
        assert response.data['result']['isError'] is True
        assert Document.objects.filter(pk=doc.id).exists()


@pytest.fixture
def superuser_client(api_client, django_user_model):
    user = django_user_model.objects.create_user(
        username='root_docs_test', password='x', is_staff=True, is_superuser=True,
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestDocumentsConnectorPanel:
    def test_panel_lists_documents_connector_with_tools(self, superuser_client, documents_connector):
        response = superuser_client.get('/api/mcp-connectors/')
        docs = next(c for c in response.data if c['slug'] == 'documents')
        tool_names = [t['name'] for t in docs['tools']]
        assert 'create_document' in tool_names
        assert 'list_folders' in tool_names
