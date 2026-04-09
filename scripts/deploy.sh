#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# scripts/deploy.sh — Deploy projectapp from repo to production
#
# Single entry point for production deployments. Replaces the manual commands
# previously documented in README.md and docs/deployment-guide.md.
#
# Usage:
#   ./scripts/deploy.sh                    # Standard deploy
#   ./scripts/deploy.sh --sync-configs     # Also sync systemd/nginx configs
#   ./scripts/deploy.sh --skip-frontend    # Skip frontend build (backend-only)
#   ./scripts/deploy.sh --yes              # Skip confirmation prompts
#   ./scripts/deploy.sh --dry-run          # Show what would be done
#
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
FRONTEND_DIR="$REPO_ROOT/frontend"
VENV="$BACKEND_DIR/venv/bin/activate"
SETTINGS="projectapp.settings_prod"

# ── Flags ─────────────────────────────────────────────────────────────────────
SYNC_CONFIGS=false
SKIP_FRONTEND=false
AUTO_YES=false
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --sync-configs)   SYNC_CONFIGS=true ;;
    --skip-frontend)  SKIP_FRONTEND=true ;;
    --yes)            AUTO_YES=true ;;
    --dry-run)        DRY_RUN=true ;;
    --help|-h)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --sync-configs   Sync systemd/nginx configs from repo to server"
      echo "  --skip-frontend  Skip frontend build (backend-only deploy)"
      echo "  --yes            Skip confirmation prompts"
      echo "  --dry-run        Show what would be done without executing"
      echo ""
      echo "Examples:"
      echo "  $0                          # Standard deploy"
      echo "  $0 --sync-configs           # Deploy + sync server configs"
      echo "  $0 --skip-frontend --yes    # Quick backend deploy, no prompts"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg (use --help for usage)"
      exit 1
      ;;
  esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
step() { echo -e "\n══════════════════════════════════════════"; echo "  $1"; echo "══════════════════════════════════════════"; }
run()  { echo "  → $*"; if [ "$DRY_RUN" = false ]; then "$@"; fi; }
confirm() {
  if [ "$AUTO_YES" = true ] || [ "$DRY_RUN" = true ]; then return 0; fi
  read -rp "  Continue? [Y/n] " answer
  [[ -z "$answer" || "$answer" =~ ^[Yy]$ ]]
}

# ── Preflight checks ─────────────────────────────────────────────────────────
if [ ! -f "$VENV" ]; then
  echo "ERROR: Virtual environment not found at $VENV"
  echo "Run initial setup first (see docs/deployment-guide.md)"
  exit 1
fi

if [ "$DRY_RUN" = true ]; then
  echo "DRY RUN — no changes will be made"
fi

# ── Step 1: Pull latest code ─────────────────────────────────────────────────
step "1/6  Pull latest code"
run git -C "$REPO_ROOT" pull origin main

# ── Step 2: Backend dependencies + migrations ────────────────────────────────
step "2/6  Backend: dependencies + migrations"
if [ "$DRY_RUN" = false ]; then
  # shellcheck disable=SC1090
  source "$VENV"
fi
run pip install -q -r "$BACKEND_DIR/requirements.txt"
run env DJANGO_SETTINGS_MODULE="$SETTINGS" python "$BACKEND_DIR/manage.py" migrate --noinput

# ── Step 3: Frontend build ───────────────────────────────────────────────────
if [ "$SKIP_FRONTEND" = true ]; then
  step "3/6  Frontend: SKIPPED (--skip-frontend)"
else
  step "3/6  Frontend: install + build"
  run npm --prefix "$FRONTEND_DIR" ci
  run npm --prefix "$FRONTEND_DIR" run build:django
fi

# ── Step 4: Collect static files ─────────────────────────────────────────────
step "4/6  Collect static files"
run env DJANGO_SETTINGS_MODULE="$SETTINGS" python "$BACKEND_DIR/manage.py" collectstatic --noinput

# ── Step 5: Sync configs (optional) ──────────────────────────────────────────
if [ "$SYNC_CONFIGS" = true ]; then
  step "5/6  Sync server configs"
  sync_args=()
  if [ "$AUTO_YES" = true ]; then sync_args+=(--yes); fi
  if [ "$DRY_RUN" = true ]; then
    echo "  (dry-run: would run sync-configs.sh)"
  else
    "$REPO_ROOT/scripts/sync-configs.sh" "${sync_args[@]}"
  fi
else
  step "5/6  Sync server configs: SKIPPED (use --sync-configs to enable)"
fi

# ── Step 6: Restart services ─────────────────────────────────────────────────
step "6/6  Restart services"
if ! confirm; then
  echo "  Aborted by user."
  exit 0
fi
run sudo systemctl restart projectapp
run sudo systemctl restart projectapp-huey

# ── Health check ──────────────────────────────────────────────────────────────
echo ""
echo "Waiting 3s for services to start..."
if [ "$DRY_RUN" = false ]; then
  sleep 3
  if curl -sf --max-time 10 https://www.projectapp.co > /dev/null 2>&1; then
    echo "✓ Health check passed — site is live"
  else
    echo "⚠ WARNING: Health check failed — verify manually:"
    echo "  sudo systemctl status projectapp"
    echo "  sudo journalctl -u projectapp -n 30"
  fi
fi

echo ""
echo "Deploy complete."
