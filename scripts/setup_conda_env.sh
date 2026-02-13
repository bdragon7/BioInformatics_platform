#!/usr/bin/env bash
set -euo pipefail

ENV_NAME=${1:-bioinfostudio}

if ! command -v conda >/dev/null 2>&1; then
  echo "Conda not found. Install Miniconda/Anaconda first."
  exit 1
fi

# ensure shell integration for 'conda activate'
eval "$(conda shell.bash hook)"

if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "Using existing conda env: $ENV_NAME"
else
  conda create -y -n "$ENV_NAME" python=3.11
fi

conda activate "$ENV_NAME"
python -m pip install --upgrade pip
python -m pip install -e '.[gui]'

echo "Conda environment ready: $ENV_NAME"
echo "Launch with: ./launch_conda.sh $ENV_NAME"
