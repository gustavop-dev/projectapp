"""Level 3: the content connector authors, validates and publishes Linktree templates."""
import base64
import json
from datetime import timedelta

import pytest
from accounts.models import Project
from django.utils import timezone

from content.models import (
    Linktree,
    LinktreeButton,
    LinktreeTemplate,
    LinktreeTemplateClick,
    LinktreeTemplateVersion,
    McpConnector,
    McpUpload,
)
from content.services.linktree_templates import service
from content.services.linktree_templates.package import store_image
from content.tests.views.test_linktree_template_views import (
    HTML,
    MANIFEST,
    image_upload,
    make_template,
    make_tree,
    make_version,
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


@pytest.fixture
def no_browser(monkeypatch):
    monkeypatch.setattr(service, 'queue_validation', lambda version_id: None)


def package_files():
    return [
        {'path': 'manifest.json', 'content': MANIFEST},
        {'path': 'template.html', 'content': HTML},
        {'path': 'template.css', 'content': 'body{margin:0}'},
    ]


def test_contract_exposes_card_variables_and_icon_search(call_content):
    """Fails if a designer cannot read the real profile, links and actions of a card by MCP."""
    tree = make_tree('mcp-contract', display_name='Ana María Ruiz', role='CEO', vcard_tel='+57 300 000 0000')
    LinktreeButton.objects.create(linktree=tree, tier='primary', action='whatsapp', label='Escríbeme', href='https://wa.me/573000000000', order=0)
    LinktreeButton.objects.create(linktree=tree, tier='row', action='email', label='Correo', href='mailto:ana@example.test', order=1)
    LinktreeButton.objects.create(linktree=tree, tier='row', action='web', label='Pendiente', href='', order=2)

    result = call_content('get_linktree_template_contract', {'linktree_id': str(tree.pk), 'icon_query': 'whatsapp'})

    card = result['linktree']
    assert card['profile']['name'] == 'Ana María Ruiz'
    assert card['profile']['initials'] == 'AM'
    assert card['primary_link'] == {'label': 'Escríbeme', 'url': 'https://wa.me/573000000000', 'icon': 'whatsapp', 'kind': 'whatsapp'}
    assert [link['label'] for link in card['links']] == ['Escríbeme', 'Correo']
    assert card['links_by_kind']['email'] == ['Correo']
    assert card['buttons_without_destination'] == ['Pendiente']
    assert 'whatsapp' in card['available_actions'] and 'email' not in card['available_actions']
    assert card['photo'] == {'available': False, 'format': None}
    assert card['branding']['accent_color'] == '#f0ff3d'
    assert 'name' in result['variables']['profile'] and 'links.whatsapp' in result['variables']['sections']
    assert 'whatsapp' in result['icons']['matches']
    assert result['example']['manifest.json']['spec'] == '1.0'


def test_upload_creates_template_and_pending_candidate(call_content, no_browser):
    """Fails if an inline package does not become a library template with a pending version."""
    tree = make_tree('mcp-upload')

    result = call_content('upload_linktree_template', {'linktree_id': str(tree.pk), 'files': package_files()})

    template = LinktreeTemplate.objects.get(pk=result['template']['id'])
    assert template.owner_id == tree.pk and template.html == HTML and template.css == 'body{margin:0}'
    version = LinktreeTemplateVersion.objects.get(pk=result['version']['id'])
    assert version.status == 'pending' and version.template_id == template.pk
    assert 'get_linktree_template_version' in result['version']['next_step']
    assert result['version']['profile_current'] is True


def test_upload_reports_package_errors_with_file_and_line(call_content, no_browser):
    """Fails if a rejected package does not tell the author which file and rule failed."""
    tree = make_tree('mcp-upload-bad')
    files = [{'path': 'manifest.json', 'content': MANIFEST}, {'path': 'template.html', 'content': '<main>{{name}}</main>'}]

    error = call_content('upload_linktree_template', {'linktree_id': str(tree.pk), 'files': files}, expect_error=True)

    assert error['code'] == 'INVALID_TEMPLATE'
    issue = error['details']['issues'][0]
    assert issue['file'] == 'template.html' and 'links' in issue['message']
    assert not LinktreeTemplate.objects.filter(owner=tree).exists()
    assert not tree.template_versions.exists()


def test_upload_requires_exactly_one_source_per_file(call_content, no_browser):
    """Fails if an ambiguous file entry is silently accepted."""
    tree = make_tree('mcp-upload-ambiguous')
    files = [{'path': 'manifest.json', 'content': MANIFEST}, {'path': 'template.html', 'content': HTML, 'base64': 'AA=='}]

    error = call_content('upload_linktree_template', {'linktree_id': str(tree.pk), 'files': files}, expect_error=True)

    assert error['code'] == 'VALIDATION_ERROR'
    assert 'template.html' in error['message']


def test_upload_is_blocked_while_a_validation_is_pending(call_content, no_browser):
    """Fails if a conversation can queue two browser validations for the same card."""
    tree = make_tree('mcp-upload-pending')
    make_version(tree, make_template(tree), status='pending')

    error = call_content('upload_linktree_template', {'linktree_id': str(tree.pk), 'files': package_files()}, expect_error=True)

    assert error['code'] == 'INVALID_TEMPLATE'
    assert error['details']['issues'][0]['code'] == 'validation_pending'


def test_validate_creates_fresh_candidate_from_library_template(call_content, no_browser):
    """Fails if re-validating with current data does not create a new immutable candidate."""
    tree = make_tree('mcp-validate')
    template = make_template(tree)
    previous = make_version(tree, template)

    result = call_content('validate_linktree_template', {'linktree_id': str(tree.pk), 'template_id': str(template.pk)})

    assert result['id'] != str(previous.pk) and result['status'] == 'pending'
    assert LinktreeTemplateVersion.objects.filter(pk=result['id'], template=template).exists()
    error = call_content('validate_linktree_template', {'linktree_id': str(tree.pk)}, expect_error=True)
    assert 'template_id o version_id' in error['message']


def test_validate_cannot_use_another_owners_template(call_content, no_browser):
    """Fails if knowing a template UUID bypasses the per-card library filter."""
    other = make_template(make_tree('mcp-other-owner'))
    tree = make_tree('mcp-validate-foreign')

    error = call_content('validate_linktree_template', {'linktree_id': str(tree.pk), 'template_id': str(other.pk)}, expect_error=True)

    assert error['code'] == 'NOT_FOUND'
    assert not tree.template_versions.exists()


def test_get_template_returns_source_and_asset_metadata(call_content):
    """Fails if a conversation cannot read the package it needs to iterate on."""
    tree = make_tree('mcp-get-template')
    template = make_template(tree, editable=True)

    result = call_content('get_linktree_template', {'linktree_id': str(tree.pk), 'template_id': str(template.pk)})

    assert result['html'] == HTML and result['manifest']['editable_assets'] == ['hero']
    assert result['assets'] == [{'key': 'hero', 'alt': 'Banner', 'format': None, 'width': None, 'height': None, 'editable': True, 'role': ''}]


def test_version_detail_flags_stale_profile(call_content):
    """Fails if a version validated with old data is reported as ready to publish."""
    tree = make_tree('mcp-version-stale')
    version = make_version(tree, make_template(tree), status='valid')
    version.report = {'issues': [{'severity': 'warning', 'code': 'unused_asset', 'message': 'x'}]}
    version.save(update_fields=['report'])
    tree.role = 'Nuevo rol'
    tree.save(update_fields=['role'])

    result = call_content('get_linktree_template_version', {'linktree_id': str(tree.pk), 'version_id': str(version.pk)})

    assert result['status'] == 'valid' and result['profile_current'] is False
    assert 'validate_linktree_template' in result['next_step']
    assert result['report']['issues'][0]['code'] == 'unused_asset'
    assert 'contact' not in result['profile']


def test_preview_returns_signed_document_and_screenshot_artifacts(call_content):
    """Fails if the preview cannot be inspected by conversation without a panel session."""
    tree = make_tree('mcp-preview')
    version = make_version(tree, make_template(tree), status='valid')
    raw = image_upload().read()
    version.screenshots = {'320': store_image({1: raw, 2: raw, 3: raw}, {'mime': 'image/png'})['paths']['1']}
    version.save(update_fields=['screenshots'])

    result = call_content('preview_linktree_template', {'linktree_id': str(tree.pk), 'version_id': str(version.pk)})

    assert result['document'].startswith('<html>')
    artifact = result['screenshot_artifacts']['320']
    assert artifact['content_type'] == 'image/png' and '/api/mcp-assets/' in artifact['download_url']
    assert McpUpload.objects.filter(pk=artifact['asset_id'], status=McpUpload.STATUS_COMPLETE).exists()


def test_publish_requires_confirmation_and_activates_the_version(call_content):
    """Fails if a template goes live without the confirmation step or the validation guard."""
    tree = make_tree('mcp-publish')
    version = make_version(tree, make_template(tree), status='valid')

    preview = call_content('publish_linktree_template', {'linktree_id': str(tree.pk), 'version_id': str(version.pk)})

    assert preview['confirmation_required'] is True
    assert preview['impact']['resources'] == {'linktree_id': str(tree.pk), 'version_id': str(version.pk)}
    tree.refresh_from_db()
    assert tree.active_template_version_id is None
    confirmed = call_content('confirm_action', {'confirmation_id': preview['confirmation_id']})
    assert confirmed['result']['active'] is True
    tree.refresh_from_db()
    version.refresh_from_db()
    assert tree.active_template_version_id == version.pk and version.published_at is not None


def test_publish_rejects_an_unvalidated_version(call_content):
    """Fails if confirmation lets an invalid snapshot reach the public URL."""
    tree = make_tree('mcp-publish-invalid')
    version = make_version(tree, make_template(tree), status='invalid')

    preview = call_content('publish_linktree_template', {'linktree_id': str(tree.pk), 'version_id': str(version.pk)})
    error = call_content('confirm_action', {'confirmation_id': preview['confirmation_id']}, expect_error=True)

    assert error['code'] == 'INVALID_TEMPLATE'
    assert error['details']['issues'][0]['code'] == 'not_validated'
    tree.refresh_from_db()
    assert tree.active_template_version_id is None


def test_reset_returns_to_the_basic_theme(call_content):
    """Fails if resetting does not clear the active template while keeping history."""
    tree = make_tree('mcp-reset')
    version = make_version(tree, make_template(tree), status='valid', published=True)
    tree.active_template_version = version
    tree.save(update_fields=['active_template_version'])

    result = call_content('reset_linktree_template', {'linktree_id': str(tree.pk)})

    assert result == {'linktree_id': str(tree.pk), 'active_version_id': None, 'previous_version_id': str(version.pk)}
    tree.refresh_from_db()
    assert tree.active_template_version_id is None and tree.template_versions.count() == 1


def test_override_asset_with_base64_then_reset(call_content, no_browser):
    """Fails if an editable image cannot be replaced and restored by conversation."""
    tree = make_tree('mcp-override')
    version = make_version(tree, make_template(tree, editable=True), status='valid')
    encoded = base64.b64encode(image_upload().read()).decode('ascii')

    replaced = call_content('override_linktree_template_asset', {
        'linktree_id': str(tree.pk), 'version_id': str(version.pk), 'key': 'hero',
        'base64': encoded, 'filename': 'hero.png',
    })

    assert replaced['status'] == 'pending' and replaced['editable_assets'][0]['overridden'] is True
    candidate = LinktreeTemplateVersion.objects.get(pk=replaced['id'])
    assert candidate.assets['hero']['paths']['1']
    # The next candidate can only be cut once the browser finished with this one.
    LinktreeTemplateVersion.objects.filter(pk=candidate.pk).update(status='valid')
    restored = call_content('override_linktree_template_asset', {
        'linktree_id': str(tree.pk), 'version_id': replaced['id'], 'key': 'hero', 'reset': True,
    })
    assert restored['editable_assets'][0]['overridden'] is False
    error = call_content('override_linktree_template_asset', {
        'linktree_id': str(tree.pk), 'version_id': str(version.pk), 'key': 'missing', 'reset': True,
    }, expect_error=True)
    assert error['code'] == 'INVALID_TEMPLATE'


def test_share_requires_a_project_and_persists_the_client(call_content, admin_user):
    """Fails if a template can be shared without a client or with another card's template."""
    tree = make_tree('mcp-share')
    template = make_template(tree)

    error = call_content('share_linktree_template', {'linktree_id': str(tree.pk), 'template_id': str(template.pk), 'is_shared': True}, expect_error=True)
    assert error['code'] == 'CONFLICT'

    tree.project = Project.objects.create(name='Share project', client=admin_user)
    tree.save(update_fields=['project'])
    result = call_content('share_linktree_template', {'linktree_id': str(tree.pk), 'template_id': str(template.pk), 'is_shared': True})

    assert result['is_shared'] is True
    template.refresh_from_db()
    assert template.client_id == admin_user.pk
    foreign = make_tree('mcp-share-foreign')
    error = call_content('share_linktree_template', {'linktree_id': str(foreign.pk), 'template_id': str(template.pk), 'is_shared': False}, expect_error=True)
    assert error['code'] == 'NOT_FOUND'


def test_clicks_aggregate_by_link_for_the_active_version(call_content):
    """Fails if click counters are not readable per link for the published snapshot."""
    tree = make_tree('mcp-clicks')
    LinktreeButton.objects.create(linktree=tree, tier='row', action='web', label='Sitio', href='https://example.test', order=0)
    version = make_version(tree, make_template(tree), status='valid', published=True)
    tree.active_template_version = version
    tree.save(update_fields=['active_template_version'])
    key = version.profile['buttons'][0]['key']
    today = timezone.localdate()
    LinktreeTemplateClick.objects.create(version=version, link_key=key, day=today, count=3)
    LinktreeTemplateClick.objects.create(version=version, link_key=key, day=today - timedelta(days=1), count=2)
    LinktreeTemplateClick.objects.create(version=version, link_key=key, day=today - timedelta(days=40), count=9)

    result = call_content('get_linktree_template_clicks', {'linktree_id': str(tree.pk)})

    assert result['version_id'] == str(version.pk) and result['total'] == 5
    assert result['links'] == [{'link_key': key, 'label': 'Sitio', 'count': 5}]
    assert len(result['daily']) == 2


def test_unknown_linktree_is_reported_as_not_found(call_content):
    """Fails if a bad identifier crashes instead of returning a readable error."""
    error = call_content('list_linktree_templates', {'linktree_id': 'not-a-uuid'}, expect_error=True)
    assert error['code'] == 'VALIDATION_ERROR'
    error = call_content('list_linktree_templates', {'linktree_id': '00000000-0000-0000-0000-000000000000'}, expect_error=True)
    assert error['code'] == 'NOT_FOUND'
    assert not Linktree.objects.exists()
