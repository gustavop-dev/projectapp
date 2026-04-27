#!/usr/bin/env bash
# Generate a Django session for Playwright smoke tests on panel pages.
#
# Usage:  bash frontend/scripts/playwright-login.sh [admin-email]
#
# Run this once per Django session (~2 weeks TTL by default).
# Re-run whenever you get 401 errors navigating to /panel via Playwright.
#
# HOW AUTHENTICATION WORKS WITH playwright/mcp
# ─────────────────────────────────────────────
# @playwright/mcp uses launchPersistentContext internally, which ignores the
# --storage-state flag entirely.  The correct flow is:
#
#   1. Run this script to create a fresh session and save the key.
#   2. At the start of a smoke-test session, ask Claude:
#        "inject the panel session cookie"
#      Claude will call browser_evaluate to set the sessionid cookie, then
#      navigate to /panel — which loads authenticated.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STATE_FILE="$REPO_ROOT/frontend/.playwright-auth/state.json"

echo "=== Playwright auth setup ==="
echo

VENV="$REPO_ROOT/backend/venv/bin/activate"
# shellcheck disable=SC1090
source "$VENV"
python "$REPO_ROOT/frontend/scripts/gen-playwright-auth.py" "${1:-}" "$STATE_FILE"

echo
echo "Session saved to: $STATE_FILE"
echo "To authenticate: ask Claude to inject the panel session cookie before navigating."
