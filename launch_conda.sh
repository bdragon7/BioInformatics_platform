#!/usr/bin/env bash
set -euo pipefail

ENV_NAME=${1:-bioinfostudio}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v conda >/dev/null 2>&1; then
  echo "Conda not found. Install Miniconda/Anaconda first."
  exit 1
fi

eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"
export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/src"
python main.py "${@:2}"
