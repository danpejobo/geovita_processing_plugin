#!/usr/bin/env bash
set -euo pipefail

# Hardcoded project root (Codex clones here)
ROOT_DIR="/workspace/geovita_processing_plugin"
echo "Using hardcoded project root: $ROOT_DIR"

# --- Backend setup ---
if [ -d "$ROOT_DIR" ]; then
  echo "Setting up Python ..."
  cd "$ROOT_DIR"

  # Setup venv
  python3 -m venv .venv

  # shellcheck disable=SC1091
  source .venv/bin/activate 
  echo "✔  Created virtual environment in .venv/"

  # Update pip
  python3 -m pip install --upgrade pip

  # Install dependencies
  pip install -r requirements.txt
  pip install -r REQUIREMENTS_TESTING.txt
  pip install -e .
  echo "✔  Dependencies installed"
else
  echo "ERROR: directory not found in $ROOT_DIR"
  exit 1
fi

# --- Done ---
cat <<'INFO'

✅ Setup complete.
To start tests run:
  pytest  # from .
INFO