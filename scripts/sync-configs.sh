#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# scripts/sync-configs.sh — Sync server configs from repo to system
#
# Compares repo configs with deployed versions, shows diffs, and copies
# changed files after confirmation. Reloads systemd/nginx as needed.
#
# Usage: ./scripts/sync-configs.sh [--yes]
#   --yes   Skip confirmation prompts (for use in scripts)
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AUTO_YES=false

for arg in "$@"; do
  case "$arg" in
    --yes) AUTO_YES=true ;;
    --help|-h)
      echo "Usage: $0 [--yes]"
      echo "  Syncs systemd and nginx configs from repo to system."
      echo "  --yes  Skip confirmation prompts"
      exit 0
      ;;
  esac
done

# ── Config mapping: repo path → system path ──────────────────────────────────
declare -A CONFIG_MAP=(
  ["$REPO_ROOT/scripts/systemd/projectapp.service"]="/etc/systemd/system/projectapp.service"
  ["$REPO_ROOT/scripts/systemd/projectapp.socket"]="/etc/systemd/system/projectapp.socket"
  ["$REPO_ROOT/scripts/systemd/huey.service"]="/etc/systemd/system/projectapp-huey.service"
  ["$REPO_ROOT/scripts/nginx/projectapp.conf"]="/etc/nginx/sites-available/projectapp"
)

systemd_changed=false
nginx_changed=false
any_changed=false

echo "═══════════════════════════════════════════════════════════"
echo "  Config Sync: repo → server"
echo "═══════════════════════════════════════════════════════════"
echo ""

for repo_file in "${!CONFIG_MAP[@]}"; do
  system_file="${CONFIG_MAP[$repo_file]}"
  short_name="$(basename "$repo_file")"

  if [ ! -f "$repo_file" ]; then
    echo "⚠  SKIP: $short_name — repo file not found"
    continue
  fi

  if [ ! -f "$system_file" ]; then
    echo "●  NEW:  $short_name → $system_file (not yet deployed)"
    any_changed=true
    if [[ "$system_file" == *systemd* ]]; then systemd_changed=true; fi
    if [[ "$system_file" == *nginx* ]]; then nginx_changed=true; fi

    if [ "$AUTO_YES" = true ]; then
      sudo cp "$repo_file" "$system_file"
      echo "   Copied."
    else
      read -rp "   Copy? [y/N] " answer
      if [[ "$answer" =~ ^[Yy]$ ]]; then
        sudo cp "$repo_file" "$system_file"
        echo "   Copied."
      else
        echo "   Skipped."
      fi
    fi
    continue
  fi

  if diff -q "$repo_file" "$system_file" > /dev/null 2>&1; then
    echo "✓  OK:   $short_name — identical"
  else
    echo "●  DIFF: $short_name"
    diff --color=auto -u "$system_file" "$repo_file" || true
    echo ""
    any_changed=true
    if [[ "$system_file" == *systemd* ]]; then systemd_changed=true; fi
    if [[ "$system_file" == *nginx* ]]; then nginx_changed=true; fi

    if [ "$AUTO_YES" = true ]; then
      sudo cp "$repo_file" "$system_file"
      echo "   Copied."
    else
      read -rp "   Apply repo version to server? [y/N] " answer
      if [[ "$answer" =~ ^[Yy]$ ]]; then
        sudo cp "$repo_file" "$system_file"
        echo "   Copied."
      else
        echo "   Skipped."
      fi
    fi
  fi
done

echo ""

# ── Post-copy actions ────────────────────────────────────────────────────────
if [ "$systemd_changed" = true ]; then
  echo "Reloading systemd daemon..."
  sudo systemctl daemon-reload
  echo "Done."
fi

if [ "$nginx_changed" = true ]; then
  echo "Testing nginx configuration..."
  if sudo nginx -t 2>&1; then
    echo "Reloading nginx..."
    sudo systemctl reload nginx
    echo "Done."
  else
    echo "ERROR: nginx config test failed — NOT reloading."
    exit 1
  fi
fi

if [ "$any_changed" = false ]; then
  echo "All configs are in sync. Nothing to do."
fi
