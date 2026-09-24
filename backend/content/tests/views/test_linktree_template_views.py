"""Panel and public API contracts for immutable Linktree templates."""
import json
from io import BytesIO

import pytest
from accounts.models import Project
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from content.models import Linktree, LinktreeTemplate, LinktreeTemplateVersion
from content.services.linktree_templates import service
from content.services.linktree_templates.render import profile_data, profile_digest

pytestmark = pytest.mark.django_db

HTML = '<main><h1>{{name}}</h1>{{#links}}<a data-link href="{{url}}">{{label}}</a>{{/links}}</main>'
MANIFEST = {
    'spec': '1.0', 'name': 'Editorial', 'assets': [], 'editable_assets': [],
    'fonts': [], 'motion': False, 'max_width': 480, 'slots': {},
}


def make_tree(handle, **fields):
    return Linktree.objects.create(handle=handle, name=handle.title(), **fields)


def make_template(tree, *, editable=False, shared=False):
    manifest = dict(MANIFEST)
    assets = {}
    if editable:
        manifest.update({
            'assets': [{'key': 'hero', 'file': 'assets/hero.png', 'alt': 'Banner'}],
            'editable_assets': ['hero'],
        })
        assets = {'hero': {'alt': 'Banner'}}
    return LinktreeTemplate.objects.create(
        owner=tree, client=tree.project.client if tree.project_id else None,
        name='Editorial', manifest=manifest, html=HTML, assets=assets, is_shared=shared,
    )


def make_version(tree, template, *, status='valid', published=False, digest=None, overrides=None):
    profile = profile_data(tree)
    return LinktreeTemplateVersion.objects.create(
        linktree=tree, template=template, profile=profile,
        profile_digest=digest or profile_digest(profile), status=status,
        document='<html><body>template</body></html>', overrides=overrides or [],
        published_at=timezone.now() if published else None,
    )


def image_upload(name='replacement.png'):
    buffer = BytesIO()
    Image.new('RGB', (24, 24), 'blue').save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


def uploaded_package():
    return {
        'manifest.json': SimpleUploadedFile('manifest.json', json.dumps(MANIFEST).encode()),
        'template.html': SimpleUploadedFile('template.html', HTML.encode()),
        'template.css': SimpleUploadedFile('template.css', b''),
    }


def test_template_library_denies_anonymous_metadata_enumeration(api_client):
    """Fails if an anonymous caller can enumerate template version metadata."""
    tree = make_tree('anonymous-library')

    response = api_client.get(reverse('linktree-template-library', args=[tree.pk]))

    assert response.status_code in (401, 403)


def test_template_library_upload_creates_pending_version_with_editor_summary(admin_client, monkeypatch):
    """Fails if a valid upload does not become an editor-visible pending version."""
    tree = make_tree('upload-template')
    monkeypatch.setattr(service, 'queue_validation', lambda version_id: None)

    response = admin_client.post(
        reverse('linktree-template-library', args=[tree.pk]), uploaded_package(), format='multipart'
    )

    assert response.status_code == 201
    assert response.data['status'] == 'pending'
    assert response.data['template_id']
    assert response.data['preview_url'].endswith('/preview/')
    assert LinktreeTemplateVersion.objects.filter(pk=response.data['id'], linktree=tree).exists()


def test_template_library_reports_missing_manifest_file(admin_client):
    """Fails if malformed packages lose the manifest.json location in their error."""
    tree = make_tree('missing-manifest')
    package = {'template.html': SimpleUploadedFile('template.html', HTML.encode())}

    response = admin_client.post(
        reverse('linktree-template-library', args=[tree.pk]), package, format='multipart'
    )

    assert response.status_code == 400
    assert response.data['issues'][0]['file'] == 'manifest.json'


def test_publish_refuses_stale_profile_without_replacing_active_version(admin_client):
    """Fails if publication accepts a version rendered from an obsolete profile snapshot."""
    tree = make_tree('stale-profile')
    template = make_template(tree)
    active = make_version(tree, template, published=True)
    tree.active_template_version = active
    tree.display_name = 'Changed after validation'
    tree.save(update_fields=['active_template_version', 'display_name', 'updated_at'])
    candidate = make_version(tree, template, digest='0' * 64)

    response = admin_client.post(reverse('linktree-template-publish', args=[tree.pk, candidate.pk]))

    assert response.status_code == 400
    assert response.data['issues'][0]['code'] == 'profile_changed'
    tree.refresh_from_db()
    assert tree.active_template_version_id == active.pk


def test_asset_override_creates_new_version_without_mutating_prior_snapshot(admin_client, monkeypatch):
    """Fails if replacing an editable asset changes a historical version in place."""
    tree = make_tree('asset-override')
    template = make_template(tree, editable=True)
    previous = make_version(tree, template)
    monkeypatch.setattr(service, 'queue_validation', lambda version_id: None)

    response = admin_client.post(
        reverse('linktree-template-override', args=[tree.pk, previous.pk, 'hero']),
        {'image': image_upload()}, format='multipart',
    )

    assert response.status_code == 201
    assert response.data['editable_assets'][0]['key'] == 'hero'
    assert response.data['editable_assets'][0]['overridden'] is True
    previous.refresh_from_db()
    assert previous.overrides == []


def test_share_template_requires_owner_tree_project_link(admin_client):
    """Fails if an unlinked Linktree can share a template beyond a client boundary."""
    tree = make_tree('unlinked-owner')
    template = make_template(tree)

    response = admin_client.post(
        reverse('linktree-template-share', args=[tree.pk, template.pk]), {'is_shared': True}, format='json'
    )

    assert response.status_code == 400
    assert response.data['detail'] == 'Vincula el Linktree a un proyecto antes de compartir.'


def test_reset_template_keeps_version_history(admin_client):
    """Fails if resetting the theme deletes the immutable template audit history."""
    tree = make_tree('reset-history')
    version = make_version(tree, make_template(tree), published=True)
    tree.active_template_version = version
    tree.save(update_fields=['active_template_version', 'updated_at'])

    response = admin_client.post(reverse('linktree-template-reset', args=[tree.pk]))

    assert response.status_code == 200
    assert response.data == {'active_version_id': None}
    assert LinktreeTemplateVersion.objects.filter(pk=version.pk).exists()


@pytest.mark.parametrize(
    ('status', 'published', 'expected_url'),
    [
        ('pending', False, None),
        ('valid', False, None),
        ('valid', True, '/api/linktrees/public/template-url/template/'),
    ],
)
def test_public_linktree_advertises_template_only_when_renderable(api_client, status, published, expected_url):
    """Fails if public JSON advertises an HTML URL whose endpoint would return 404."""
    tree = make_tree('template-url')
    version = make_version(tree, make_template(tree), status=status, published=published)
    tree.active_template_version = version
    tree.save(update_fields=['active_template_version', 'updated_at'])

    response = api_client.get(reverse('public-linktree', args=[tree.handle]))

    assert response.status_code == 200
    assert response.data['template_url'] == expected_url


def test_same_client_project_can_see_shared_template_in_library(admin_client, admin_user):
    """Fails if templates shared by a client disappear from that client's other projects."""
    owner_project = Project.objects.create(name='Owner project', client=admin_user)
    owner = make_tree('same-client-owner', project=owner_project)
    template = make_template(owner, shared=True)
    recipient_project = Project.objects.create(name='Recipient project', client=admin_user)
    recipient = make_tree('same-client-recipient', project=recipient_project)

    response = admin_client.get(reverse('linktree-template-library', args=[recipient.pk]))

    assert response.status_code == 200
    assert [row['id'] for row in response.data['templates']] == [template.pk]


def test_different_client_project_cannot_see_shared_template_in_library(admin_client, admin_user, django_user_model):
    """Fails if a shared template leaks from one client to another client's project."""
    owner_project = Project.objects.create(name='Owner client', client=admin_user)
    owner = make_tree('different-client-owner', project=owner_project)
    make_template(owner, shared=True)
    other_client = django_user_model.objects.create_user(username='other-client', email='other@example.test')
    recipient_project = Project.objects.create(name='Other client', client=other_client)
    recipient = make_tree('different-client-recipient', project=recipient_project)

    response = admin_client.get(reverse('linktree-template-library', args=[recipient.pk]))

    assert response.status_code == 200
    assert response.data['templates'] == []


def test_publish_valid_version_activates_public_template(admin_client, api_client):
    """Fails if a validated version cannot become the active publicly rendered template."""
    tree = make_tree('publish-success')
    version = make_version(tree, make_template(tree))

    response = admin_client.post(reverse('linktree-template-publish', args=[tree.pk, version.pk]))

    assert response.status_code == 200
    tree.refresh_from_db()
    assert tree.active_template_version_id == version.pk
    public = api_client.get(reverse('linktree-template-public', args=[tree.handle]))
    assert public.status_code == 200
    assert "default-src 'none'" in public['Content-Security-Policy']


def test_private_asset_preview_remains_admin_only(api_client):
    """Fails if a private template asset can be downloaded without panel authentication."""
    tree = make_tree('private-asset')
    version = make_version(tree, make_template(tree, editable=True))

    response = api_client.get(reverse('linktree-template-asset-preview', args=[tree.pk, version.pk, 'hero']))

    assert response.status_code in (401, 403)


def test_public_template_refuses_pending_active_version(api_client):
    """Fails if a pending template draft can be rendered on the public Linktree URL."""
    tree = make_tree('pending-public')
    version = make_version(tree, make_template(tree), status='pending')
    tree.active_template_version = version
    tree.save(update_fields=['active_template_version', 'updated_at'])

    response = api_client.get(reverse('linktree-template-public', args=[tree.handle]))

    assert response.status_code == 404
