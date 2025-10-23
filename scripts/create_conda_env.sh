#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

if ! command -v conda >/dev/null 2>&1; then
  cat <<'MSG'
conda (miniforge/miniconda) not found. Install Miniforge for Apple Silicon:
  https://github.com/conda-forge/miniforge

After installing, re-run this script.
MSG
  exit 1
fi

echo "Creating conda environment 'portodash' from environment.yml..."
conda env create -f environment.yml || {
  echo "Failed to create conda env. If the env already exists, try: conda env update -f environment.yml --prune";
  exit 1
}

cat <<MSG
Environment created. Activate it with:

  conda activate portodash

Then run the app:

  streamlit run app.py

MSG
