#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found. Install Python 3.11+ first."
  exit 1
fi

python3 -m pip install --upgrade pip
python3 -m pip install -e '.[gui]'

echo "Spyder-compatible environment is ready (current python3)."
echo "If Spyder uses a different interpreter, configure it in Spyder preferences."
