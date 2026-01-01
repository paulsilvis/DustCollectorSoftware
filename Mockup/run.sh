#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# Prefer the venv python if it exists; otherwise fall back.
PY="$PROJECT_ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY="$(command -v python3 || true)"
fi
if [[ -z "${PY:-}" ]]; then
  echo "ERROR: python not found (expected .venv or python3 in PATH)" >&2
  exit 1
fi

# Config can be overridden by env; otherwise default.
CONFIG="${CONFIG:-config/config.yaml}"

# Resolve HW_MODE from env, without clobbering caller overrides.
# Priority:
#   1) HW_MODE explicit (real|mock)
#   2) MOCK boolean-ish (true/false/1/0/yes/no/on/off)
#   3) default mock
_hw_mode_from_mock() {
  local v="${1,,}"
  case "$v" in
    1|true|yes|on)  echo "mock" ;;
    0|false|no|off) echo "real" ;;
    *)
      echo "ERROR: invalid MOCK value '$1' (use true/false)" >&2
      exit 2
      ;;
  esac
}

if [[ -n "${HW_MODE-}" ]]; then
  case "${HW_MODE,,}" in
    mock|real) : ;;
    *)
      echo "ERROR: invalid HW_MODE '$HW_MODE' (use mock|real)" >&2
      exit 2
      ;;
  esac
else
  if [[ -n "${MOCK-}" ]]; then
    HW_MODE="$(_hw_mode_from_mock "$MOCK")"
  else
    HW_MODE="mock"
  fi
fi

echo "== DustCollector run =="
echo "HW_MODE=$HW_MODE"
echo "CONFIG=$CONFIG"
echo "PY=$PY"
echo

# Export the env var your Python actually reads.
export DUSTCOLLECTOR_HW="$HW_MODE"

# Preserve CONFIG for convenience/debugging (Python still gets --config).
export CONFIG

exec "$PY" -m src.main --config "$CONFIG" "$@"
