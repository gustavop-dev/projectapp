"""Panel API for the per-card image library."""
import pytest
from django.urls import reverse

from content.services.linktree_templates import library
from content.tests.views.test_linktree_template_views import image_upload, make_tree

pytestmark = pytest.mark.django_db


def test_library_denies_anonymous_access(api_client):
    """Fails if library images or metadata are reachable without a staff session."""
    tree = make_tree('assets-anonymous')
    library.upload_asset(tree, 'hero', '', image_upload())

    listing = api_client.get(reverse('linktree-assets', args=[tree.pk]))
    preview = api_client.get(reverse('linktree-asset', args=[tree.pk, 'hero']))

    assert listing.status_code in (401, 403)
    assert preview.status_code in (401, 403)


def test_upload_lists_and_previews_a_library_image(admin_client):
    """Fails if the panel cannot add an image and read it back at the URL templates use."""
    tree = make_tree('assets-upload')

    response = admin_client.post(
        reverse('linktree-assets', args=[tree.pk]),
        {'key': 'hero', 'alt': 'Fondo', 'image': image_upload('hero.png')}, format='multipart',
    )

    assert response.status_code == 201
    assert response.data['url'] == f'/api/linktrees/admin/{tree.pk}/assets/hero/'
    listing = admin_client.get(reverse('linktree-assets', args=[tree.pk]))
    assert [row['key'] for row in listing.data['assets']] == ['hero']
    preview = admin_client.get(response.data['url'])
    assert preview.status_code == 200 and preview['Content-Type'] == 'image/webp'


def test_upload_rejects_a_bad_key_with_an_issue(admin_client):
    """Fails if the panel accepts a key the template syntax cannot reference."""
    tree = make_tree('assets-bad-key')

    response = admin_client.post(
        reverse('linktree-assets', args=[tree.pk]),
        {'key': 'Hero Image', 'image': image_upload()}, format='multipart',
    )

    assert response.status_code == 400
    assert response.data['issues'][0]['code'] == 'invalid_key'
    assert not tree.assets.exists()


def test_delete_removes_the_library_entry(admin_client):
    """Fails if deleting does not free the key for a later upload."""
    tree = make_tree('assets-delete')
    library.upload_asset(tree, 'hero', '', image_upload())

    response = admin_client.delete(reverse('linktree-asset', args=[tree.pk, 'hero']))

    assert response.status_code == 204
    assert not tree.assets.exists()
    assert admin_client.delete(reverse('linktree-asset', args=[tree.pk, 'hero'])).status_code == 400
