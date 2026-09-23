"""The content connector manages the per-card image library used by HTML designs."""
import base64
import json

import pytest

from content.models import LinktreeTemplate, McpConnector
from content.services.linktree_templates import library, service
from content.tests.views.test_linktree_template_views import (
    HTML,
    MANIFEST,
    image_upload,
    make_tree,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def call_content(api_client, superuser):
    connector, _ = McpConnector.objects.get_or_create(slug='content', defaults={'name': 'Content'})
    connector.is_active = True
    connector.save()
    token = connector.generate_token()

    def call(name, arguments, *, expect_error=False):
        response = api_client.post(f'/api/mcp/content/{token}/', {
            'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
            'params': {'name': name, 'arguments': arguments},
        }, format='json')
        result = response.data['result']
        assert result['isError'] is expect_error, result['content'][0]['text']
        if expect_error:
            return result['structuredContent']['error']
        return json.loads(result['content'][0]['text'])
    return call


def test_upload_returns_url_and_markup_for_the_design(call_content):
    """Fails if a conversation cannot obtain a reference to use inside its HTML."""
    tree = make_tree('mcp-asset-upload')
    encoded = base64.b64encode(image_upload().read()).decode('ascii')

    result = call_content('upload_linktree_asset', {
        'linktree_id': str(tree.pk), 'key': 'hero', 'alt': 'Fondo', 'base64': encoded, 'filename': 'hero.png',
    })

    assert result['url'] == f'/api/linktrees/admin/{tree.pk}/assets/hero/'
    assert result['markup'] == {'html': '<img data-asset="hero">', 'css': 'asset(hero)'}
    assert result['width'] == 24 and result['sanitized'] is False
    listed = call_content('list_linktree_assets', {'linktree_id': str(tree.pk)})
    assert [row['key'] for row in listed['assets']] == ['hero']
    contract = call_content('get_linktree_template_contract', {'linktree_id': str(tree.pk)})
    assert contract['linktree']['assets'][0]['key'] == 'hero'


def test_template_can_use_the_returned_url(call_content, monkeypatch):
    """Fails if the design cannot reference the library image by its URL."""
    tree = make_tree('mcp-asset-template')
    monkeypatch.setattr(service, 'queue_validation', lambda version_id: None)
    asset, _ = library.upload_asset(tree, 'hero', '', image_upload())
    files = [
        {'path': 'manifest.json', 'content': MANIFEST},
        {'path': 'template.html', 'content': HTML + f'<img src="{asset.url}">'},
        {'path': 'template.css', 'content': f'main{{background:url({asset.url})}}'},
    ]

    result = call_content('upload_linktree_template', {'linktree_id': str(tree.pk), 'files': files})

    template = LinktreeTemplate.objects.get(pk=result['template']['id'])
    assert '<img data-asset="hero">' in template.html and template.css == 'main{background:asset(hero)}'
    assert template.manifest['library_assets'] == ['hero']
    source = call_content('get_linktree_template', {'linktree_id': str(tree.pk), 'template_id': str(template.pk)})
    assert source['library_assets'] == ['hero']


def test_upload_rejects_invalid_key_and_ambiguous_sources(call_content):
    """Fails if a bad key or two payloads slip through as a library image."""
    tree = make_tree('mcp-asset-invalid')
    encoded = base64.b64encode(image_upload().read()).decode('ascii')

    error = call_content('upload_linktree_asset', {'linktree_id': str(tree.pk), 'key': 'Hero', 'base64': encoded}, expect_error=True)
    assert error['code'] == 'INVALID_TEMPLATE' and error['details']['issues'][0]['code'] == 'invalid_key'

    error = call_content('upload_linktree_asset', {'linktree_id': str(tree.pk), 'key': 'hero'}, expect_error=True)
    assert error['code'] == 'VALIDATION_ERROR'
    assert not tree.assets.exists()


def test_delete_requires_confirmation(call_content):
    """Fails if a library image disappears without the confirmation step."""
    tree = make_tree('mcp-asset-delete')
    library.upload_asset(tree, 'hero', '', image_upload())

    preview = call_content('delete_linktree_asset', {'linktree_id': str(tree.pk), 'key': 'hero'})

    assert preview['confirmation_required'] is True
    assert tree.assets.filter(key='hero').exists()
    confirmed = call_content('confirm_action', {'confirmation_id': preview['confirmation_id']})
    assert confirmed['result']['deleted'] is True
    assert not tree.assets.exists()
