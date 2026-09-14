"""Which settings module a process lands on when none is exported."""

import importlib
import os
import subprocess
import sys

import pytest
from django.conf import settings

from projectapp.environment import default_settings_module


def _import_in_subprocess(module, django_env):
    """Import ``module`` in a fresh interpreter with DJANGO_ENV exported."""
    env = {key: value for key, value in os.environ.items() if key != 'DJANGO_SETTINGS_MODULE'}
    env['DJANGO_ENV'] = django_env
    return subprocess.run(
        [sys.executable, '-c', f'import {module}'],
        cwd=settings.BASE_DIR, env=env, capture_output=True, text=True, timeout=60,
    )


def test_production_env_selects_prod_settings():
    assert default_settings_module({'DJANGO_ENV': 'production'}) == 'projectapp.settings_prod'


@pytest.mark.parametrize('environ', [
    {},
    {'DJANGO_ENV': 'development'},
    {'DJANGO_ENV': 'staging'},
    {'DJANGO_ENV': ''},
])
def test_any_other_env_selects_dev_settings(environ):
    assert default_settings_module(environ) == 'projectapp.settings_dev'


def test_manage_py_derives_the_settings_module_from_django_env(monkeypatch):
    import manage

    argv_seen = []
    monkeypatch.delenv('DJANGO_SETTINGS_MODULE', raising=False)
    monkeypatch.setenv('DJANGO_ENV', 'production')
    monkeypatch.setattr('django.core.management.execute_from_command_line', argv_seen.append)

    manage.main()

    assert os.environ['DJANGO_SETTINGS_MODULE'] == 'projectapp.settings_prod'
    assert argv_seen == [sys.argv]


def test_manage_py_keeps_an_exported_settings_module(monkeypatch):
    import manage

    monkeypatch.setenv('DJANGO_SETTINGS_MODULE', 'projectapp.settings_build')
    monkeypatch.setenv('DJANGO_ENV', 'production')
    monkeypatch.setattr('django.core.management.execute_from_command_line', lambda argv: None)

    manage.main()

    assert os.environ['DJANGO_SETTINGS_MODULE'] == 'projectapp.settings_build'


def test_asgi_derives_the_settings_module_from_django_env(monkeypatch):
    monkeypatch.delenv('DJANGO_SETTINGS_MODULE', raising=False)
    monkeypatch.setenv('DJANGO_ENV', 'production')
    monkeypatch.setattr('django.core.asgi.get_asgi_application', lambda: 'asgi-app')
    monkeypatch.delitem(sys.modules, 'projectapp.asgi', raising=False)

    asgi = importlib.import_module('projectapp.asgi')
    sys.modules.pop('projectapp.asgi')  # never leave the stubbed module behind

    assert asgi.application == 'asgi-app'
    assert os.environ['DJANGO_SETTINGS_MODULE'] == 'projectapp.settings_prod'


def test_settings_dev_refuses_to_load_when_django_env_is_production():
    result = _import_in_subprocess('projectapp.settings_dev', 'production')

    assert result.returncode == 1
    assert 'ImproperlyConfigured' in result.stderr
    assert 'DJANGO_SETTINGS_MODULE=projectapp.settings_prod' in result.stderr


def test_settings_dev_loads_outside_production():
    result = _import_in_subprocess('projectapp.settings_dev', 'development')

    assert result.returncode == 0, result.stderr
