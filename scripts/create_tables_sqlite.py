#!/usr/bin/env python3
"""Create minimal project-related tables in SQLite when Alembic can't run.

This script creates the following tables if they do not exist:
- project
- context
- orchestrationrun
- generatedartifact

It is intended as a lightweight fallback for local development only.
"""
import json
import sqlite3
import sys
from pathlib import Path


def create_tables(db_path: str):
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS project (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            metadata JSON,
            owner_id TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS context (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            key TEXT,
            value JSON,
            updated_at TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES project(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orchestrationrun (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            status TEXT,
            steps JSON,
            started_at TIMESTAMP,
            finished_at TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES project(id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS generatedartifact (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            run_id TEXT,
            name TEXT NOT NULL,
            path TEXT,
            content JSON,
            metadata JSON,
            created_at TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES project(id),
            FOREIGN KEY(run_id) REFERENCES orchestrationrun(id)
        )
        """
    )

    conn.commit()
    conn.close()


def main(argv):
    if len(argv) < 2:
        print("Usage: create_tables_sqlite.py <db_path>")
        return 2
    db_path = argv[1]
    create_tables(db_path)
    print(f"Created/ensured tables in {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
