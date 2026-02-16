#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -x "$SCRIPT_DIR/python/python" ]]; then
  "$SCRIPT_DIR/python/python" main.py "$@"
else
  python main.py "$@"
fi
