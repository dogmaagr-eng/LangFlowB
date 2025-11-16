#!/usr/bin/env bash
set -euo pipefail

# Minimal DB init script for local development (SQLite + Alembic)
# Usage: ./scripts/init_db.sh [--venv .venv] [--db ./langflow.db]

VENV_DIR=".venv"
DB_PATH="./langflow.db"

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --venv)
      VENV_DIR="$2"
      shift 2
      ;;
    --db)
      DB_PATH="$2"
      shift 2
      ;;
    --install-backend)
      INSTALL_BACKEND=1
      shift 1
      ;;
    -h|--help)
      echo "Usage: $0 [--venv .venv] [--db ./langflow.db] [--install-backend]"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1"
      exit 1
      ;;
  esac
done

echo "Using venv: ${VENV_DIR}"
echo "Using sqlite db: ${DB_PATH}"

python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

pip install --upgrade pip

# Minimal Python deps to create DB and run alembic migrations
pip install "sqlmodel>=0.0.8" alembic sqlalchemy aiosqlite orjson

# Optional: if you prefer a complete install of the backend package (may take longer),
# uncomment the following line or run it manually:
# Optionally install the full backend package in editable mode. This may pull many
# dependencies (and may fail on Python version mismatches). Use only if you want
# the full environment and have a compatible Python version (3.10/3.11).
if [ "${INSTALL_BACKEND-0}" = "1" ]; then
  echo "Installing backend package in editable mode (this may take several minutes)..."
  pip install -e src/backend/base
else
  echo "Skipping editable backend install (use --install-backend to enable)."
fi

# Export DB URL for Alembic / Langflow configuration
export LANGFLOW_DATABASE_URL="sqlite:///${DB_PATH}"

echo "Applying Alembic migrations (using config at src/backend/base/langflow/alembic.ini)"
# Ensure langflow package can be imported by Alembic (set PYTHONPATH to repo src dirs)
REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
export PYTHONPATH="${REPO_ROOT}/src/backend/base:${REPO_ROOT}/src:${REPO_ROOT}/src/lfx/src:${PYTHONPATH-}"

set +e
echo "Attempting to run Alembic migrations (best-effort). If this fails we'll apply a lightweight fallback."
python3 - <<PY
import os
from alembic.config import Config
from alembic import command

cfg_path = os.path.join("${REPO_ROOT}", "src/backend/base/langflow/alembic.ini")
cfg = Config(cfg_path)
script_dir = os.path.join("${REPO_ROOT}", "src/backend/base/langflow", "alembic")
# Ensure alembic knows the absolute script location (avoid relative path issues)
cfg.set_main_option('script_location', script_dir)
command.upgrade(cfg, "head")
PY
ALEMBIC_EXIT=$?
set -e

if [ $ALEMBIC_EXIT -ne 0 ]; then
  echo "Alembic failed (exit=$ALEMBIC_EXIT). Falling back to direct SQLite table creation."
  python3 "${REPO_ROOT}/scripts/create_tables_sqlite.py" "${DB_PATH}"
else
  echo "Alembic migrations applied successfully."
fi

echo "Database initialized at ${DB_PATH}"
echo "You can now run the backend (ensure PYTHONPATH includes src/backend/base and src)."
