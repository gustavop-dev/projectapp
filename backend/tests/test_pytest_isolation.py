"""The pytest session never reaches production files, queues or caches.

backend/pytest.ini runs the suite on projectapp.settings_test, and
backend/conftest.py refuses to start a session that could touch production
(the refusals live in tests/isolation.py). These tests pin both halves.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from content.models import FinancingAgreement
from tests.isolation import (
    collect_storage_locations,
    deployed_clone_refusal,
    settings_refusals,
    storage_refusals,
)

SAFE_SETTINGS = {
    'SETTINGS_MODULE': 'projectapp.settings_test',
    'IS_PRODUCTION': False,
    'DATABASES': {'default': {'ENGINE': 'django.db.backends.sqlite3'}},
    'CACHES': {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    'HUEY': SimpleNamespace(immediate=True),
}

# Exported values win over a checkout's backend/.env, so they are dropped
# before importing settings in a subprocess.
DOTENV_OVERRIDES = ('DJANGO_ENV', 'DJANGO_SETTINGS_MODULE', 'REDIS_URL', 'CACHE_REDIS_URL')


def _checkout_with_linked_dotenv(tmp_path, *, main_clone, django_env):
    """A checkout whose backend/.env symlinks a deployed .env, as worktrees do."""
    deployed_env = tmp_path / 'deployed.env'
    deployed_env.write_text(f'DJANGO_ENV={django_env}\n')
    backend = tmp_path / 'checkout' / 'backend'
    backend.mkdir(parents=True)
    (backend / '.env').symlink_to(deployed_env)
    git_marker = backend.parent / '.git'
    if main_clone:
        git_marker.mkdir()
    else:
        git_marker.write_text('gitdir: /srv/repo/.git/worktrees/session\n')
    return backend


def _import_settings_in(backend, module):
    """Import ``module`` from ``backend`` in a fresh interpreter and report it."""
    env = {key: value for key, value in os.environ.items() if key not in DOTENV_OVERRIDES}
    code = f'import {module} as s; print(s.IS_PRODUCTION, s.CACHES["default"]["BACKEND"])'
    return subprocess.run(
        [sys.executable, '-c', code],
        cwd=backend, env=env, capture_output=True, text=True, timeout=60,
    )


def test_default_storage_saves_under_the_session_temp_root():
    name = default_storage.save('isolation/probe.txt', ContentFile(b'probe'))
    path = Path(default_storage.path(name))

    assert path.read_bytes() == b'probe'
    assert path.is_relative_to(settings.TEST_FILE_ROOT)
    assert not path.is_relative_to(settings.BASE_DIR)
    default_storage.delete(name)


def test_private_file_field_saves_under_the_session_temp_root():
    """The field evaluated its callable storage at import, before any fixture."""
    storage = FinancingAgreement._meta.get_field('signed_document').storage
    name = storage.save('isolation/probe.pdf', ContentFile(b'%PDF-1.4 probe'))
    path = Path(storage.path(name))

    assert path.read_bytes() == b'%PDF-1.4 probe'
    assert path.is_relative_to(Path(settings.TEST_FILE_ROOT) / 'private_media')
    storage.delete(name)


def test_dbbackup_storage_writes_under_the_session_temp_root():
    """django-dbbackup copies STORAGES['dbbackup'] when it is first imported."""
    from dbbackup.storage import get_storage

    location = Path(get_storage().storage.location)

    assert location == Path(settings.TEST_FILE_ROOT) / 'dbbackup'


def test_guard_sees_the_storage_bound_at_import_inside_the_temp_root():
    """The settings half of the guard runs at session start, before any override."""
    locations = collect_storage_locations()

    assert locations['content.FinancingAgreement.signed_document'] == str(
        Path(settings.TEST_FILE_ROOT) / 'private_media'
    )
    assert storage_refusals(settings.TEST_FILE_ROOT, settings.BASE_DIR, locations) == []


def test_settings_refusals_accept_the_suite_configuration():
    assert settings_refusals(SimpleNamespace(**SAFE_SETTINGS), {}) == []


@pytest.mark.parametrize(('override', 'named'), [
    ({'SETTINGS_MODULE': 'projectapp.settings_prod'}, 'projectapp.settings_prod'),
    ({'IS_PRODUCTION': True}, 'IS_PRODUCTION'),
    ({'DATABASES': {'default': {'ENGINE': 'django.db.backends.mysql'}}}, 'django.db.backends.mysql'),
    (
        {'CACHES': {'default': {'BACKEND': 'django.core.cache.backends.redis.RedisCache'}}},
        'django.core.cache.backends.redis.RedisCache',
    ),
    ({'HUEY': SimpleNamespace(immediate=False)}, 'immediate mode'),
])
def test_settings_refusals_name_each_production_signal(override, named):
    reasons = settings_refusals(SimpleNamespace(**{**SAFE_SETTINGS, **override}), {})

    assert len(reasons) == 1
    assert named in reasons[0]


@pytest.mark.parametrize('name', ['REDIS_URL', 'CACHE_REDIS_URL'])
def test_settings_refusals_reject_an_exported_redis_url(name):
    reasons = settings_refusals(SimpleNamespace(**SAFE_SETTINGS), {name: 'redis://localhost:6379/5'})

    assert len(reasons) == 1
    assert name in reasons[0]


def test_storage_refusals_flag_a_location_outside_the_temp_root(tmp_path):
    root, checkout = tmp_path / 'session', tmp_path / 'checkout'

    reasons = storage_refusals(root, checkout, {
        'MEDIA_ROOT': str(checkout / 'media'),
        'PRIVATE_MEDIA_ROOT': str(root / 'private_media'),
    })

    assert len(reasons) == 1
    assert reasons[0].startswith('MEDIA_ROOT ')


def test_storage_refusals_reject_a_temp_root_inside_the_checkout(tmp_path):
    checkout = tmp_path / 'backend'

    reasons = storage_refusals(checkout / 'tmp', checkout, {'MEDIA_ROOT': str(checkout / 'tmp' / 'media')})

    assert len(reasons) == 1
    assert 'inside the checkout' in reasons[0]


@pytest.mark.parametrize(('main_clone', 'django_env', 'refused'), [
    (True, 'production', True),
    (False, 'production', False),
    (True, 'development', False),
])
def test_deployed_clone_refusal_hits_only_a_main_clone_declaring_production(
    tmp_path, main_clone, django_env, refused,
):
    backend = _checkout_with_linked_dotenv(tmp_path, main_clone=main_clone, django_env=django_env)

    assert (deployed_clone_refusal(backend) is not None) is refused


def test_suite_settings_ignore_a_symlinked_production_dotenv(tmp_path):
    """Worktrees symlink the deployed backend/.env: base settings read it, the suite's must not."""
    backend = _checkout_with_linked_dotenv(tmp_path, main_clone=False, django_env='production')
    with (tmp_path / 'deployed.env').open('a') as dotenv:
        dotenv.write('CACHE_REDIS_URL=redis://localhost:6379/1\n')
    package = backend / 'projectapp'
    package.mkdir()
    (package / '__init__.py').write_text('')
    for name in ('settings.py', 'settings_test.py'):
        shutil.copy(Path(settings.BASE_DIR) / 'projectapp' / name, package / name)

    base = _import_settings_in(backend, 'projectapp.settings')
    suite = _import_settings_in(backend, 'projectapp.settings_test')

    assert base.stdout.split() == ['True', 'django.core.cache.backends.redis.RedisCache'], base.stderr
    assert suite.stdout.split() == ['False', 'django.core.cache.backends.locmem.LocMemCache'], suite.stderr
