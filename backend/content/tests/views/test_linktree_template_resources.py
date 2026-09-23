"""Private previews and public access to immutable template assets."""
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

import html5lib
import pytest
from django.core import signing
from django.urls import reverse
from freezegun import freeze_time

from content.services.linktree_templates.package import store_image
from content.services.linktree_templates.render import asset_token, asset_url, render_document
from content.tests.views.test_linktree_template_views import image_upload, make_template, make_tree, make_version

pytestmark = pytest.mark.django_db


@pytest.fixture
def resource_version():
    tree = make_tree('template-resources')
    template = make_template(tree, editable=True)
    template.html += '<img data-asset="hero">'
    template.save(update_fields=['html'])
    version = make_version(tree, template)
    raw = image_upload().read()
    version.assets = {'hero': store_image({1: raw, 2: raw, 3: raw}, {'mime': 'image/png', 'alt': 'Banner'})}
    version.screenshots = {'320': version.assets['hero']['paths']['1']}
    version.document = render_document(version)
    version.save(update_fields=['assets', 'screenshots', 'document'])
    return version


@pytest.fixture
def published_resource(resource_version):
    resource_version.published_at = datetime(2026, 9, 23, tzinfo=timezone.utc)
    resource_version.save(update_fields=['published_at'])
    return resource_version


def test_published_asset_streams_original_image(api_client, published_resource):
    """Fails if public image delivery changes the immutable image bytes."""
    response = api_client.get(asset_url(published_resource, 'hero'))

    assert response.status_code == 200
    assert response['Content-Type'] == 'image/png'
    assert b''.join(response.streaming_content) == image_upload().read()


def test_unpublished_asset_requires_preview_signature(api_client, resource_version):
    """Fails if an unpublished candidate exposes its image without a signature."""
    response = api_client.get(asset_url(resource_version, 'hero'))

    assert response.status_code == 404


def test_signed_preview_serves_unpublished_image(api_client, resource_version):
    """Fails if an authorized preview cannot load its private image."""
    response = api_client.get(asset_url(resource_version, 'hero'), {'preview': asset_token(resource_version)})

    assert response.status_code == 200
    assert b''.join(response.streaming_content) == image_upload().read()


@pytest.mark.parametrize('token', ['invalid', signing.dumps('another-version', salt='linktree-template-preview')])
def test_preview_rejects_signature_for_wrong_version(api_client, resource_version, token):
    """Fails if a malformed or cross-version token grants private image access."""
    response = api_client.get(asset_url(resource_version, 'hero'), {'preview': token})

    assert response.status_code == 404


def test_expired_preview_signature_is_rejected(api_client, resource_version):
    """Fails if preview images remain accessible after the one-hour expiry."""
    with freeze_time('2026-09-23 10:00:00'):
        token = asset_token(resource_version)

    with freeze_time('2026-09-23 11:00:01'):
        response = api_client.get(asset_url(resource_version, 'hero'), {'preview': token})

    assert response.status_code == 404


def test_inactive_linktree_hides_published_asset(api_client, published_resource):
    """Fails if deactivating a Linktree leaves its images publicly accessible."""
    tree = published_resource.linktree
    tree.is_active = False
    tree.save(update_fields=['is_active'])

    response = api_client.get(asset_url(published_resource, 'hero'))

    assert response.status_code == 404


@pytest.mark.parametrize(('key', 'density'), [('missing', 1), ('hero', 4)])
def test_public_asset_rejects_missing_variant(api_client, published_resource, key, density):
    """Fails if unknown image keys or densities escape as a server error."""
    response = api_client.get(asset_url(published_resource, key, density))

    assert response.status_code == 404


def test_preview_html_signs_asset_urls(admin_client, resource_version):
    """Fails if preview HTML leaks unsigned assets or enables template scripts."""
    url = reverse('linktree-template-preview', args=[resource_version.linktree_id, resource_version.pk])

    response = admin_client.get(url)

    assert response.status_code == 200
    document = html5lib.parse(response.content.decode(), namespaceHTMLElements=False)
    src = document.find('.//img').get('src')
    token = parse_qs(urlsplit(src).query)['preview'][0]
    assert signing.loads(token, salt='linktree-template-preview', max_age=3600) == str(resource_version.pk)
    assert "script-src 'none'" in response['Content-Security-Policy']
    assert '; sandbox' in response['Content-Security-Policy']


def test_screenshot_streams_private_capture(admin_client, resource_version):
    """Fails if the editor cannot retrieve its saved viewport capture."""
    url = reverse('linktree-template-screenshot', args=[resource_version.linktree_id, resource_version.pk, 320])

    response = admin_client.get(url)

    assert response.status_code == 200
    assert response['Cache-Control'] == 'private, no-store'
    assert b''.join(response.streaming_content) == image_upload().read()


def test_missing_screenshot_returns_not_found(admin_client, resource_version):
    """Fails if an absent capture produces a broken file response."""
    url = reverse('linktree-template-screenshot', args=[resource_version.linktree_id, resource_version.pk, 375])

    response = admin_client.get(url)

    assert response.status_code == 404


def test_missing_stored_asset_returns_not_found(api_client, published_resource):
    """Fails if a removed storage file causes a public server error."""
    published_resource.assets['hero']['paths']['1'] = 'missing/image.png'
    published_resource.save(update_fields=['assets'])

    response = api_client.get(asset_url(published_resource, 'hero'))

    assert response.status_code == 404


def test_editable_asset_preview_streams_private_image(admin_client, resource_version):
    """Fails if the image editor cannot retrieve a declared editable asset."""
    url = reverse('linktree-template-asset-preview', args=[resource_version.linktree_id, resource_version.pk, 'hero'])

    response = admin_client.get(url)

    assert response.status_code == 200
    assert b''.join(response.streaming_content) == image_upload().read()


def test_noneditable_asset_has_no_editor_preview(admin_client, resource_version):
    """Fails if a noneditable image appears through the editor asset endpoint."""
    template = resource_version.template
    template.manifest['editable_assets'] = []
    template.save(update_fields=['manifest'])
    url = reverse('linktree-template-asset-preview', args=[resource_version.linktree_id, resource_version.pk, 'hero'])

    response = admin_client.get(url)

    assert response.status_code == 404
