#!/usr/bin/env python3
"""
Generate a Playwright storage-state JSON with a valid Django admin session.

Usage:
    python frontend/scripts/gen-playwright-auth.py
    python frontend/scripts/gen-playwright-auth.py admin@example.com
    python frontend/scripts/gen-playwright-auth.py admin@example.com /custom/path/state.json

The output file is loaded by the Playwright MCP via --storage-state so every
browser session starts already authenticated.  Add the output path to .gitignore.
"""
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / 'backend'
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectapp.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore

User = get_user_model()

# --- Resolve args ---
email = sys.argv[1] if len(sys.argv) > 1 else input('Admin email: ').strip()
output_path = Path(sys.argv[2] if len(sys.argv) > 2 else REPO_ROOT / 'frontend' / '.playwright-auth' / 'state.json')

# --- Look up user ---
try:
    user = User.objects.get(email__iexact=email)
except User.DoesNotExist:
    print(f'Error: no user found with email {email!r}', file=sys.stderr)
    sys.exit(1)

if not user.is_staff:
    print(f'Warning: {email} is not a staff user — panel pages may still redirect to login.', file=sys.stderr)

# --- Create a new session ---
session = SessionStore()
session['_auth_user_id'] = str(user.pk)
session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
session['_auth_user_hash'] = user.get_session_auth_hash()
session.save()

# --- Write Playwright storage state ---
# Nuxt dev server proxies /api and /admin to Django, so cookies for "localhost"
# are sent with all proxied requests — no port mismatch in practice.
state = {
    'cookies': [
        {
            'name': 'sessionid',
            'value': session.session_key,
            'domain': 'localhost',
            'path': '/',
            'expires': -1,
            'httpOnly': True,
            'secure': False,
            'sameSite': 'Lax',
        },
    ],
    'origins': [],
}

output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(state, indent=2))

print(f'Session key : {session.session_key}')
print(f'User        : {user.email} (staff={user.is_staff})')
print(f'State file  : {output_path}')
print()
print('NOTE: @playwright/mcp uses launchPersistentContext which ignores --storage-state.')
print('Inject the cookie manually at the start of each smoke test session:')
print()
print(f'  document.cookie = "sessionid={session.session_key}; path=/; SameSite=Lax";')
print()
print('Or ask Claude to run inject_panel_session() before navigating to /panel.')
