"""Pre-flight refusals that keep a pytest session away from production.

backend/conftest.py runs them at session start and aborts on any finding.
They take the settings, environment and paths as arguments, so the refusals
themselves are tested (tests/test_pytest_isolation.py).
"""

from pathlib import Path

from decouple import RepositoryEnv

TEST_SETTINGS_MODULE = 'projectapp.settings_test'
SAFE_CACHE_BACKENDS = frozenset({
    'django.core.cache.backends.dummy.DummyCache',
    'django.core.cache.backends.locmem.LocMemCache',
})
REDIS_URL_VARIABLES = ('REDIS_URL', 'CACHE_REDIS_URL')


def settings_refusals(settings, environ):
    """Why these settings, or this environment, could reach production."""
    reasons = []
    if settings.SETTINGS_MODULE != TEST_SETTINGS_MODULE:
        reasons.append(
            f'settings module is {settings.SETTINGS_MODULE}, not {TEST_SETTINGS_MODULE} '
            '(an exported DJANGO_SETTINGS_MODULE or --ds overrides pytest.ini)'
        )
    if getattr(settings, 'IS_PRODUCTION', False):
        reasons.append('IS_PRODUCTION is True: DJANGO_ENV=production is exported')
    engine = settings.DATABASES['default']['ENGINE']
    if engine != 'django.db.backends.sqlite3':
        reasons.append(f'database engine is {engine}; the suite runs on SQLite only')
    for alias, cache in settings.CACHES.items():
        if cache['BACKEND'] not in SAFE_CACHE_BACKENDS:
            reasons.append(
                f'cache {alias!r} uses {cache["BACKEND"]}; the suite clears its cache between tests'
            )
    if getattr(settings.HUEY, 'immediate', False) is not True:
        reasons.append('Huey is not in immediate mode: tasks would be enqueued to Redis')
    reasons.extend(
        f'{name} is exported: the suite never talks to Redis, unset it'
        for name in REDIS_URL_VARIABLES
        if name in environ
    )
    return reasons


def storage_refusals(file_root, base_dir, locations):
    """Why a file storage could write outside the session's temp root."""
    if file_root is None:
        return ['TEST_FILE_ROOT is not set: file storages point at their real locations']
    root = Path(file_root).resolve()
    if root.is_relative_to(Path(base_dir).resolve()):
        return [f'TEST_FILE_ROOT {root} is inside the checkout {base_dir}']
    return [
        f'{name} writes to {location}, outside {root}'
        for name, location in sorted(locations.items())
        if not Path(location).resolve().is_relative_to(root)
    ]


def deployed_clone_refusal(base_dir):
    """Refuse the deployed checkout: a main clone whose .env declares production.

    Session worktrees have a ``.git`` file, not a directory, even when their
    backend/.env symlinks the deployed one; CI has no .env at all.
    """
    backend = Path(base_dir)
    dotenv = backend / '.env'
    if not (backend.parent / '.git').is_dir() or not dotenv.is_file():
        return None
    # .data only: RepositoryEnv.__contains__ also looks at os.environ.
    if RepositoryEnv(str(dotenv)).data.get('DJANGO_ENV') != 'production':
        return None
    return (
        f'{backend.parent} is a deployed production checkout: run the suite '
        'from a session worktree instead'
    )


def collect_storage_locations():
    """Every directory a file storage of this process would write into."""
    from django.apps import apps
    from django.conf import settings
    from django.core.files.storage import default_storage, storages
    from django.db.models import FileField

    locations = {
        'MEDIA_ROOT': settings.MEDIA_ROOT,
        'default_storage': default_storage.location,
    }
    if getattr(settings, 'PRIVATE_MEDIA_ROOT', None):
        locations['PRIVATE_MEDIA_ROOT'] = settings.PRIVATE_MEDIA_ROOT
    for alias in settings.STORAGES:
        storage = storages[alias]
        if alias != 'staticfiles' and hasattr(storage, 'location'):
            locations[f'STORAGES[{alias}]'] = storage.location
    # A callable ``storage=`` is evaluated once, when the model class is built,
    # so a field can hold an instance that no longer follows STORAGES.
    for model in apps.get_models():
        for field in model._meta.local_fields:
            if isinstance(field, FileField) and hasattr(field.storage, 'location'):
                locations[f'{model._meta.label}.{field.name}'] = field.storage.location
    return locations
