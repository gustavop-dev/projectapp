#!/usr/bin/env bash
# Activa el virtualenv de desarrollo del backend (backend/venv).
# Uso desde la raíz del repo:  source scripts/activate-dev-env.sh
set -euo pipefail
_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_VENV="$_ROOT/backend/venv"
if [[ ! -f "$_VENV/bin/activate" ]]; then
  echo "No se encontró el venv en $_VENV" >&2
  echo "Crea el entorno con: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt" >&2
  exit 1
fi
# shellcheck source=/dev/null
source "$_VENV/bin/activate"
echo "Venv activo: $_VENV ($(command -v python)) — $(python -V 2>&1)"
