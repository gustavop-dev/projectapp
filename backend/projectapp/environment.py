"""Which settings module a process uses when DJANGO_SETTINGS_MODULE is unset."""

import os

PRODUCTION_SETTINGS_MODULE = 'projectapp.settings_prod'
DEVELOPMENT_SETTINGS_MODULE = 'projectapp.settings_dev'


def default_settings_module(environ=None):
    """Map the exported DJANGO_ENV to a settings module.

    Reads the process environment only, never backend/.env: session worktrees
    symlink the deployed .env, so honoring it here would point every worktree
    manage.py at the production database. A production host that exports
    nothing lands on settings_dev, which refuses to load there.
    """
    environ = os.environ if environ is None else environ
    if environ.get('DJANGO_ENV') == 'production':
        return PRODUCTION_SETTINGS_MODULE
    return DEVELOPMENT_SETTINGS_MODULE
