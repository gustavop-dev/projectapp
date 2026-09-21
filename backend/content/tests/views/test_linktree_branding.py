"""Branding persists through the panel API and is safe to publish."""
from io import BytesIO
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from content.models import Linktree

pytestmark = pytest.mark.django_db

@pytest.fixture
def tree():
    return Linktree.objects.create(handle='brand-test', name='Brand')

def logo_file():
    stream = BytesIO()
    Image.new('RGB', (16, 16), 'blue').save(stream, format='PNG')
    return SimpleUploadedFile('logo.png', stream.getvalue(), content_type='image/png')

def test_branding_create_update_and_public_read(admin_client, api_client):
    created = admin_client.post(reverse('create-linktree'), {
        'handle': 'custom-brand', 'name': 'Custom', 'accent_color': '#123abc',
        'font_family': 'Playfair Display',
    }, format='json')
    assert created.status_code == 201
    updated = admin_client.patch(reverse('update-linktree', args=[created.data['id']]), {
        'background_color': '#eeeeee', 'text_color': '#111111',
        'muted_color': '#666666', 'button_text_color': '#ffffff',
    }, format='json')
    assert updated.status_code == 200
    public = api_client.get(reverse('public-linktree', args=['custom-brand']))
    assert {key: public.data[key] for key in (
        'accent_color', 'font_family', 'background_color', 'text_color', 'muted_color', 'button_text_color',
    )} == {
        'accent_color': '#123abc', 'font_family': 'Playfair Display',
        'background_color': '#eeeeee', 'text_color': '#111111',
        'muted_color': '#666666', 'button_text_color': '#ffffff',
    }

@pytest.mark.parametrize('field,value', [
    ('accent_color', 'red'), ('background_color', '#fff'),
    ('text_color', 'url(https://example.com)'), ('muted_color', '#gggggg'),
    ('button_text_color', ''), ('font_family', "Ubuntu';color:red"),
    ('font_family', 'https://fonts.google.com'), ('font_family', ''),
])
def test_invalid_branding_is_not_persisted(admin_client, tree, field, value):
    response = admin_client.patch(reverse('update-linktree', args=[tree.pk]), {field: value}, format='json')
    assert response.status_code == 400
    assert field in response.data
    tree.refresh_from_db()
    assert getattr(tree, field) != value

def test_logo_upload_public_read_and_remove(admin_client, api_client, tree):
    tree.avatar = 'linktrees/avatars/existing.png'
    tree.save()
    endpoint = reverse('upload-linktree-logo', args=[tree.pk])
    upload = admin_client.post(endpoint, {'logo': logo_file()}, format='multipart')
    assert upload.status_code == 200
    public = api_client.get(reverse('public-linktree', args=[tree.handle]))
    assert public.data['logo'] == upload.data['logo']
    removed = admin_client.delete(endpoint)
    tree.refresh_from_db()
    assert removed.data['logo'] is None
    assert tree.avatar.name == 'linktrees/avatars/existing.png'

def test_fake_image_cannot_replace_logo(admin_client, tree):
    tree.logo = 'linktrees/logos/existing.png'
    tree.save()
    response = admin_client.post(reverse('upload-linktree-logo', args=[tree.pk]), {
        'logo': SimpleUploadedFile('fake.png', b'not an image', content_type='image/png'),
    }, format='multipart')
    assert response.status_code == 400
    tree.refresh_from_db()
    assert tree.logo.name == 'linktrees/logos/existing.png'

def test_logo_requires_staff(api_client, tree):
    response = api_client.post(reverse('upload-linktree-logo', args=[tree.pk]), {'logo': logo_file()}, format='multipart')
    assert response.status_code in (401, 403)
    tree.refresh_from_db()
    assert not tree.logo

def test_oversized_logo_is_rejected(admin_client, tree):
    image = SimpleUploadedFile('large.png', b'x' * (5 * 1024 * 1024 + 1), content_type='image/png')
    response = admin_client.post(reverse('upload-linktree-logo', args=[tree.pk]), {'logo': image}, format='multipart')
    assert response.status_code == 400
    assert '5MB' in response.data['logo']

def test_default_design_survives_unrelated_update(admin_client, tree):
    response = admin_client.patch(reverse('update-linktree', args=[tree.pk]), {'bio': 'New bio'}, format='json')
    assert response.data['background_color'] == '#001713'
    assert response.data['accent_color'] == '#f0ff3d'
    assert response.data['font_family'] == 'Ubuntu'
