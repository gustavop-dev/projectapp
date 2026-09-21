"""The content connector uses the same branding validation as the panel."""
import json
import pytest
from content.models import Linktree, McpConnector

pytestmark = pytest.mark.django_db

@pytest.fixture
def call_content(api_client, superuser):
    connector, _ = McpConnector.objects.get_or_create(slug='content', defaults={'name': 'Content'})
    connector.is_active = True
    connector.save()
    token = connector.generate_token()

    def call(name, arguments):
        response = api_client.post(f'/api/mcp/content/{token}/', {
            'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
            'params': {'name': name, 'arguments': arguments},
        }, format='json')
        return response.data['result']
    return call


def test_mcp_creates_and_reads_branding(call_content):
    created = call_content('create_linktree', {'data': {
        'handle': 'mcp-brand', 'name': 'MCP Brand', 'font_family': 'Lora', 'accent_color': '#abcdef',
    }})
    card = json.loads(created['content'][0]['text'])
    result = call_content('get_linktree', {'linktree_id': card['id']})
    data = json.loads(result['content'][0]['text'])
    assert data['font_family'] == 'Lora'
    assert data['accent_color'] == '#abcdef'


def test_mcp_updates_branding(call_content):
    tree = Linktree.objects.create(handle='mcp-update', name='MCP')
    call_content('update_linktree', {'linktree_id': str(tree.pk), 'data': {'font_family': 'Inter'}})
    tree.refresh_from_db()
    assert tree.font_family == 'Inter'


def test_mcp_rejects_invalid_branding(call_content):
    tree = Linktree.objects.create(handle='mcp-invalid', name='MCP')
    result = call_content('update_linktree', {'linktree_id': str(tree.pk), 'data': {'accent_color': 'red'}})
    assert result['isError'] is True
    tree.refresh_from_db()
    assert tree.accent_color == '#f0ff3d'


def test_mcp_links_and_unlinks_project(call_content, admin_user):
    from accounts.models import Project
    project = Project.objects.create(name='MCP project', client=admin_user)
    created = call_content('create_linktree', {'data': {
        'handle': 'mcp-project', 'name': 'Project link', 'project': project.pk,
    }})
    card = json.loads(created['content'][0]['text'])
    assert card['project'] == project.pk
    updated = call_content('update_linktree', {'linktree_id': card['id'], 'data': {'project': None}})
    assert json.loads(updated['content'][0]['text'])['project'] is None
    invalid = call_content('update_linktree', {'linktree_id': card['id'], 'data': {'project': 999999}})
    assert invalid['isError'] is True
    assert Linktree.objects.get(pk=card['id']).project_id is None
