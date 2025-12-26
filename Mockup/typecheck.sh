#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ ! -d "$ROOT/.venv" ]]; then
  echo "ERROR: .venv not found. Run ./install.sh first."
  exit 1
fi

# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"

echo "== ensure typecheck deps =="
pip install -q mypy types-PyYAML

echo "== mypy =="
mypy --config-file "$ROOT/mypy.ini" "$ROOT/src"
