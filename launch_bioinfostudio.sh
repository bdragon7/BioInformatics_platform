#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -x "$SCRIPT_DIR/python/python" ]]; then
  PY_EXE="$SCRIPT_DIR/python/python"
else
  PY_EXE="python"
fi

# Portable dependency guard for local Gemma inference.
if ! "$PY_EXE" -c "import llama_cpp" >/dev/null 2>&1; then
  echo "[BioInfoStudio] llama-cpp-python not found in portable runtime."
  echo "[BioInfoStudio] Local Gemma will run in fallback mode until dependency is installed."
fi

"$PY_EXE" main.py "$@"
