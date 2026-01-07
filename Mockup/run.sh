#!/usr/bin/env bash
set -euo pipefail

echo "== DustCollector run =="
CONFIG=${CONFIG:-config/config.yaml}
PY=${PY:-.venv/bin/python}

echo "CONFIG=$CONFIG"
echo "PY=$PY"
echo

exec "$PY" -m src.main --config "$CONFIG"
