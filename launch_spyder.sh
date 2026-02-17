#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/src"

if ! command -v spyder >/dev/null 2>&1; then
  echo "Spyder not found on PATH. Open Spyder manually and run main.py from this folder."
  exit 1
fi

spyder main.py
