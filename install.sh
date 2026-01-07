#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "== DustCollector install =="
echo "Project root: $PROJECT_ROOT"

if ! command -v python3 >/dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

if [[ ! -d "$PROJECT_ROOT/.venv" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv "$PROJECT_ROOT/.venv"
else
    echo "Virtual environment already exists"
fi

# shellcheck disable=SC1091
source "$PROJECT_ROOT/.venv/bin/activate"

pip install --upgrade pip >/dev/null
pip install -r "$PROJECT_ROOT/requirements.txt"

echo "Install complete."
echo "Next: chmod +x run.sh && ./run.sh"
