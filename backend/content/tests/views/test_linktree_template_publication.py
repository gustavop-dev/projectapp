"""Panel selection and public contracts of a published template snapshot."""
from datetime import datetime, timezone

import pytest
from accounts.models import Project
from django.urls import reverse
from freezegun import freeze_time

from content.models import LinktreeTemplateVersion
from content.tests.views.test_linktree_template_views import make_template, make_tree, make_version

pytestmark = pytest.mark.django_db


@pytest.fixture
def candidate():
    tree = make_tree('publication-contract')
    return make_version(tree, make_template(tree))


@pytest.mark.parametrize('field', ['template_id', 'version_id'])
def test_library_selection_creates_fresh_candidate(admin_client, candidate, field):
    """Fails if selecting saved content does not create an immutable candidate."""
    identifiers = {'template_id': candidate.template_id, 'version_id': candidate.pk}
    url = reverse('linktree-template-library', args=[candidate.linktree_id])

    response = admin_client.post(url, {field: str(identifiers[field])}, format='json')

    assert response.status_code == 201
    version = LinktreeTemplateVersion.objects.get(pk=response.data['id'])
    assert version.pk != candidate.pk
    assert version.status == 'pending'
    assert version.template_id == candidate.template_id


def test_library_selection_requires_one_identifier(admin_client, candidate):
    """Fails if an empty selection is accepted without choosing source content."""
    url = reverse('linktree-template-library', args=[candidate.linktree_id])

    response = admin_client.post(url, {}, format='json')

    assert response.status_code == 400
    assert str(response.data['non_field_errors'][0]) == 'Selecciona una plantilla o una versión.'
    assert candidate.linktree.template_versions.count() == 1


def test_library_cannot_select_another_owners_template(admin_client, candidate):
    """Fails if knowing a template UUID bypasses library ownership filtering."""
    recipient = make_tree('other-owner')
    url = reverse('linktree-template-library', args=[recipient.pk])

    response = admin_client.post(url, {'template_id': str(candidate.template_id)}, format='json')

    assert response.status_code == 404
    assert recipient.template_versions.count() == 0


def test_nonstaff_user_cannot_select_template(api_client, candidate, django_user_model):
    """Fails if a platform user can invoke the administrator template editor."""
    user = django_user_model.objects.create_user(username='template-client', email='template@example.test')
    api_client.force_authenticate(user=user)
    url = reverse('linktree-template-library', args=[candidate.linktree_id])

    response = api_client.post(url, {'template_id': str(candidate.template_id)}, format='json')

    assert response.status_code == 403
    assert candidate.linktree.template_versions.count() == 1


@pytest.mark.parametrize('shared', [True, False])
def test_owner_updates_template_sharing(admin_client, admin_user, candidate, shared):
    """Fails if sharing changes are not persisted with the owning client."""
    tree = candidate.linktree
    tree.project = Project.objects.create(name='Template project', client=admin_user)
    tree.save(update_fields=['project'])
    url = reverse('linktree-template-share', args=[tree.pk, candidate.template_id])

    response = admin_client.post(url, {'is_shared': shared}, format='json')

    assert response.status_code == 200
    candidate.template.refresh_from_db()
    assert candidate.template.is_shared is shared
    assert candidate.template.client_id == admin_user.pk


def test_asset_override_requires_image_upload(admin_client, candidate):
    """Fails if an empty image replacement request creates a candidate."""
    url = reverse('linktree-template-override', args=[candidate.linktree_id, candidate.pk, 'hero'])

    response = admin_client.post(url, {}, format='multipart')

    assert response.status_code == 400
    assert response.data['detail'] == 'Selecciona una imagen.'
    assert candidate.linktree.template_versions.count() == 1


@freeze_time('2026-09-23 10:00:00')
def test_public_clicks_aggregate_per_snapshot_link(api_client, candidate):
    """Fails if repeated clicks overwrite rather than increment the daily count."""
    candidate.published_at = datetime(2026, 9, 23, tzinfo=timezone.utc)
    candidate.profile['buttons'] = [{'key': '7', 'label': 'Visit', 'url': 'https://example.test'}]
    candidate.save(update_fields=['published_at', 'profile'])
    url = reverse('linktree-template-click', args=[candidate.pk])
    api_client.post(url, {'key': '7'}, format='json')

    response = api_client.post(url, {'key': '7'}, format='json')

    assert response.status_code == 204
    assert list(candidate.clicks.values_list('link_key', 'count')) == [('7', 2)]


@pytest.mark.parametrize('key', ['missing', 7])
def test_unknown_public_click_is_not_recorded(api_client, candidate, key):
    """Fails if unknown keys or invalid types pollute published click totals."""
    candidate.published_at = datetime(2026, 9, 23, tzinfo=timezone.utc)
    candidate.save(update_fields=['published_at'])
    url = reverse('linktree-template-click', args=[candidate.pk])

    response = api_client.post(url, {'key': key}, format='json')

    assert response.status_code == 400
    assert response.data['detail'] == 'Enlace no válido.'
    assert candidate.clicks.count() == 0


def test_enabled_pwa_manifest_uses_published_profile(api_client, candidate):
    """Fails if the PWA manifest uses mutable profile data instead of the snapshot."""
    candidate.profile.update({'pwa_enabled': True, 'name': 'Published business'})
    candidate.published_at = datetime(2026, 9, 23, tzinfo=timezone.utc)
    candidate.save(update_fields=['profile', 'published_at'])
    tree = candidate.linktree
    tree.active_template_version = candidate
    tree.display_name = 'Unpublished change'
    tree.save(update_fields=['active_template_version', 'display_name'])

    response = api_client.get(reverse('linktree-template-manifest', args=[tree.handle]))

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/manifest+json'
    assert response.json()['name'] == 'Published business'
    assert response.json()['start_url'] == tree.public_path


def test_disabled_pwa_has_no_manifest(api_client, candidate):
    """Fails if the manifest is exposed when the published profile disables PWA."""
    candidate.profile['pwa_enabled'] = False
    candidate.save(update_fields=['profile'])
    tree = candidate.linktree
    tree.active_template_version = candidate
    tree.save(update_fields=['active_template_version'])

    response = api_client.get(reverse('linktree-template-manifest', args=[tree.handle]))

    assert response.status_code == 404
