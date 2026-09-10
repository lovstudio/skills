#!/bin/zsh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV="$ROOT/.venv"

if [[ ! -x "$VENV/bin/python" ]]; then
  "$PYTHON_BIN" -m venv --system-site-packages "$VENV"
fi
"$VENV/bin/python" -m pip install --quiet --upgrade pip
"$VENV/bin/python" -m pip install --quiet requests requests_toolbelt noiseprotocol tqdm treelib
"$VENV/bin/python" -m pip install --quiet --no-deps synology-api
"$VENV/bin/python" - <<'PY'
import synology_api
from synology_api.auth import Authentication
print('sync-with-synology runtime ready')
PY
