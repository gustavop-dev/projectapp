#!/usr/bin/env bash
# Generate a Playwright auth state and (re)configure the Claude Code MCP.
#
# Usage:  bash frontend/scripts/playwright-login.sh [admin-email]
#
# Run this once per session (Django sessions expire in ~2 weeks by default).
# Re-run whenever you get auth errors in Playwright-backed smoke tests.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STATE_FILE="$REPO_ROOT/frontend/.playwright-auth/state.json"

echo "=== Playwright auth setup ==="
echo

# --- Activate venv and generate session ---
VENV="$REPO_ROOT/backend/venv/bin/activate"
# shellcheck disable=SC1090
source "$VENV"
python "$REPO_ROOT/frontend/scripts/gen-playwright-auth.py" "${1:-}" "$STATE_FILE"

echo
echo "=== Reconfiguring Playwright MCP ==="
echo

# Overwrite the MCP entry with --storage-state
claude mcp add playwright -- npx -y @playwright/mcp@latest --storage-state "$STATE_FILE"

echo
echo "Done. Restart Claude Code (or open a new session) for the MCP change to take effect."
echo "State file: $STATE_FILE"
