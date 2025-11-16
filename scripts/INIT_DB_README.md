# Init DB (local development)

This document explains how to initialize the local SQLite database for Langflow development with the migrations included in the repo.

Prerequisites
 - macOS (this project is developed and tested on macOS, including M1)
 - Python 3.10+ (you can use `python3`)

Quick start

1) From the project root, run:

```bash
./scripts/init_db.sh --venv .venv --db ./langflow.db
```

2) The script will:
 - create or reuse a virtual environment at `.venv`
 - install minimal dependencies: `sqlmodel`, `alembic`, `sqlalchemy`, `aiosqlite`
 - set `LANGFLOW_DATABASE_URL` to point to the SQLite file you provided
 - run `alembic upgrade head` using `src/backend/base/langflow/alembic.ini`

3) After the script finishes you can run the backend in development mode. Example (from repo root):

```bash
source .venv/bin/activate
export PYTHONPATH=src/backend/base:src
uvicorn langflow.main:app --reload --port 7860
```

Notes and troubleshooting
 - If `alembic` fails, verify `PYTHONPATH` and the location of `alembic.ini` used by the script.
 - For a production DB use Postgres and set `LANGFLOW_DATABASE_URL` accordingly in your environment.
