#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
PY="$PROJECT_ROOT/.venv/bin/python"

if [[ ! -x "$PY" ]]; then
    echo "ERROR: venv not found. Run ./install.sh first."
    exit 1
fi

export MOCK="${MOCK:-true}"
export CONFIG_PATH="${CONFIG_PATH:-$PROJECT_ROOT/config/config.yaml}"

echo "== DustCollector run =="
echo "MOCK=$MOCK"
echo "CONFIG=$CONFIG_PATH"
echo

exec "$PY" -m src.main --config "$CONFIG_PATH"
