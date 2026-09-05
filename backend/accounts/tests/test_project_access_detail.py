"""Behavior tests for the secure project access-detail API."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from accounts.models import ProjectAccessNote, ProjectAdminAccess
from accounts.services.credential_cipher import decrypt_secret, encrypt_secret


User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def production_access(project, admin_user):
    return ProjectAdminAccess.objects.create(
        project=project,
        environment=ProjectAdminAccess.Environment.PRODUCTION,
        admin_url='https://project.example.test/admin/',
        admin_username='root',
        admin_password_encrypted=encrypt_secret('production-secret'),
        updated_by=admin_user,
    )


@pytest.fixture
def access_notes(project, admin_user):
    regular = ProjectAccessNote.objects.create(
        project=project,
        title='Deployment owner',
        content_encrypted=encrypt_secret('ops@example.test'),
        created_by=admin_user,
        updated_by=admin_user,
    )
    sensitive = ProjectAccessNote.objects.create(
        project=project,
        title='Recovery token',
        content_encrypted=encrypt_secret('recovery-secret'),
        is_sensitive=True,
        created_by=admin_user,
        updated_by=admin_user,
    )
    return regular, sensitive


def platform_url(project):
    return f'/api/accounts/projects/{project.pk}/access/'


def test_detail_returns_fixed_environments_with_masked_secrets(
    api_client, admin_headers, project, production_access,
):
    response = api_client.get(platform_url(project), **admin_headers)

    assert response.status_code == 200
    environments = response.json()['environments']
    assert [item['environment'] for item in environments] == ['production', 'staging']
    assert environments[0]['has_password'] is True
    assert 'admin_password' not in environments[0]
    assert 'production-secret' not in response.content.decode()
    assert response['Cache-Control'] == 'no-store, max-age=0'


def test_detail_returns_plain_content_only_for_regular_notes(
    api_client, admin_headers, project, access_notes,
):
    response = api_client.get(platform_url(project), **admin_headers)

    notes = {item['title']: item for item in response.json()['notes']}
    assert notes['Deployment owner']['content'] == 'ops@example.test'
    assert notes['Recovery token']['content'] == ''
    assert notes['Recovery token']['has_content'] is True


def test_password_update_stores_ciphertext(api_client, admin_headers, project):
    response = api_client.patch(
        platform_url(project),
        {'environment': 'staging', 'admin_password': 'staging-secret'},
        format='json',
        **admin_headers,
    )

    access = ProjectAdminAccess.objects.get(project=project, environment='staging')
    assert response.status_code == 200
    assert access.admin_password_encrypted != 'staging-secret'
    assert decrypt_secret(access.admin_password_encrypted) == 'staging-secret'
    assert 'staging-secret' not in response.content.decode()


def test_password_reveal_uses_no_store_cache_header(
    api_client, admin_headers, project, production_access,
):
    response = api_client.post(
        f'{platform_url(project)}environments/production/password/reveal/',
        {},
        format='json',
        **admin_headers,
    )

    assert response.status_code == 200
    assert response.json() == {'secret': 'production-secret'}
    assert response['Cache-Control'] == 'no-store, max-age=0'
    assert response['Pragma'] == 'no-cache'


def test_password_delete_removes_ciphertext(
    api_client, admin_headers, project, production_access,
):
    response = api_client.delete(
        f'{platform_url(project)}environments/production/password/',
        **admin_headers,
    )

    production_access.refresh_from_db()
    assert response.status_code == 200
    assert production_access.admin_password_encrypted == ''
    assert response.json()['environments'][0]['has_password'] is False


def test_field_update_rejects_multiple_values(api_client, admin_headers, project):
    response = api_client.patch(
        platform_url(project),
        {
            'environment': 'production',
            'site_url': 'https://project.example.test',
            'admin_url': 'https://project.example.test/admin/',
        },
        format='json',
        **admin_headers,
    )

    assert response.status_code == 400
    assert response.json()['non_field_errors'] == ['Guarda exactamente un campo por solicitud.']


def test_field_update_rejects_ftp_url(api_client, admin_headers, project):
    response = api_client.patch(
        platform_url(project),
        {'repository_url': 'ftp://files.example.test/project'},
        format='json',
        **admin_headers,
    )

    assert response.status_code == 400
    assert 'repository_url' in response.json()


def test_note_create_stores_ciphertext(api_client, admin_headers, project):
    response = api_client.post(
        f'{platform_url(project)}notes/',
        {'title': 'API key', 'content': 'note-secret', 'is_sensitive': True},
        format='json',
        **admin_headers,
    )

    note = ProjectAccessNote.objects.get(project=project)
    response_note = response.json()['notes'][0]
    assert response.status_code == 201
    assert note.content_encrypted != 'note-secret'
    assert decrypt_secret(note.content_encrypted) == 'note-secret'
    assert response_note['content'] == ''


def test_note_create_rejects_unknown_fields(api_client, admin_headers, project):
    response = api_client.post(
        f'{platform_url(project)}notes/',
        {
            'title': 'API key',
            'content': 'note-secret',
            'is_sensitive': True,
            'plaintext_backup': 'must-not-be-accepted',
        },
        format='json',
        **admin_headers,
    )

    assert response.status_code == 400
    assert ProjectAccessNote.objects.filter(project=project).exists() is False


def test_sensitive_note_reveal_uses_no_store_cache_header(
    api_client, admin_headers, project, access_notes,
):
    sensitive_note = access_notes[1]
    response = api_client.post(
        f'{platform_url(project)}notes/{sensitive_note.pk}/reveal/',
        {},
        format='json',
        **admin_headers,
    )

    assert response.status_code == 200
    assert response.json()['secret'] == 'recovery-secret'
    assert response['Cache-Control'] == 'no-store, max-age=0'


def test_note_update_persists_content(api_client, admin_headers, project, access_notes):
    regular_note = access_notes[0]
    response = api_client.patch(
        f'{platform_url(project)}notes/{regular_note.pk}/',
        {'content': 'new operational context'},
        format='json',
        **admin_headers,
    )

    regular_note.refresh_from_db()
    assert response.status_code == 200
    assert decrypt_secret(regular_note.content_encrypted) == 'new operational context'
    assert response.json()['notes'][1]['content'] == 'new operational context'


def test_note_delete_removes_record(api_client, admin_headers, project, access_notes):
    regular_note = access_notes[0]
    response = api_client.delete(
        f'{platform_url(project)}notes/{regular_note.pk}/',
        **admin_headers,
    )

    assert response.status_code == 200
    assert ProjectAccessNote.objects.filter(pk=regular_note.pk).exists() is False
    assert len(response.json()['notes']) == 1


def test_legacy_classification_moves_values(api_client, admin_headers, project):
    project.admin_url = 'https://legacy.example.test/admin/'
    project.admin_username = 'legacy-root'
    project.admin_password_encrypted = encrypt_secret('legacy-secret')
    project.save(update_fields=['admin_url', 'admin_username', 'admin_password_encrypted'])

    response = api_client.post(
        f'{platform_url(project)}legacy/classify/',
        {'environment': 'production'},
        format='json',
        **admin_headers,
    )

    project.refresh_from_db()
    access = ProjectAdminAccess.objects.get(project=project, environment='production')
    assert response.status_code == 200
    assert access.admin_username == 'legacy-root'
    assert decrypt_secret(access.admin_password_encrypted) == 'legacy-secret'
    assert project.admin_password_encrypted == ''
    assert response.json()['legacy_access'] is None


def test_legacy_classification_conflict_returns_409(
    api_client, admin_headers, project, production_access,
):
    project.admin_url = 'https://legacy.example.test/admin/'
    project.save(update_fields=['admin_url'])

    response = api_client.post(
        f'{platform_url(project)}legacy/classify/',
        {'environment': 'production'},
        format='json',
        **admin_headers,
    )

    project.refresh_from_db()
    production_access.refresh_from_db()
    assert response.status_code == 409
    assert response.json()['code'] == 'project_access_classification_conflict'
    assert project.admin_url == 'https://legacy.example.test/admin/'
    assert production_access.admin_url == 'https://project.example.test/admin/'


def test_client_role_cannot_read_detail(api_client, client_headers, project):
    response = api_client.get(platform_url(project), **client_headers)

    assert response.status_code == 403


def test_platform_session_authentication_is_rejected(api_client, admin_user, project):
    api_client.force_login(admin_user)

    response = api_client.get(platform_url(project))

    assert response.status_code == 401


def test_panel_staff_can_read_detail(api_client, admin_user, project):
    admin_user.is_staff = True
    admin_user.save(update_fields=['is_staff'])
    api_client.force_login(admin_user)

    response = api_client.get(f'/api/projects/{project.pk}/access/')

    assert response.status_code == 200
    assert response.json()['project']['id'] == project.pk


def test_panel_nonstaff_cannot_read_detail(api_client, admin_user, project):
    api_client.force_login(admin_user)

    response = api_client.get(f'/api/projects/{project.pk}/access/')

    assert response.status_code == 403


def test_environment_constraint_rejects_duplicate(project, production_access):
    with pytest.raises(IntegrityError), transaction.atomic():
        ProjectAdminAccess.objects.create(
            project=project,
            environment=ProjectAdminAccess.Environment.PRODUCTION,
        )
