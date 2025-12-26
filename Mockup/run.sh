#!/usr/bin/env bash
set -euo pipefail

# ----------------------------
# DustCollector launcher
# ----------------------------

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# Config path (override with CONFIG_PATH=...)
CONFIG_PATH="${CONFIG_PATH:-config/config.yaml}"

# Hardware mode:
#   mock | real
# Default: mock (safe)
HW_MODE="${DUSTCOLLECTOR_HW:-mock}"

if [[ "$HW_MODE" != "mock" && "$HW_MODE" != "real" ]]; then
    echo "ERROR: DUSTCOLLECTOR_HW must be 'mock' or 'real'"
    exit 1
fi

export DUSTCOLLECTOR_HW="$HW_MODE"

VENV_PY="$PROJECT_ROOT/.venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
    echo "ERROR: venv python not found at: $VENV_PY"
    echo "Run: ./install.sh"
    exit 1
fi

echo "== DustCollector run =="
echo "HW_MODE=$HW_MODE"
echo "CONFIG=$CONFIG_PATH"
echo "PY=$VENV_PY"
echo

exec "$VENV_PY" -m src.main --config "$CONFIG_PATH"
