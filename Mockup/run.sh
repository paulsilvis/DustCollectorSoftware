#!/usr/bin/env bash
set -euo pipefail

# ----------------------------
# DustCollector launcher
# ----------------------------

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

echo "== DustCollector run =="
echo "HW_MODE=$HW_MODE"
echo "CONFIG=$CONFIG_PATH"
echo

exec python -m src.main --config "$CONFIG_PATH"
