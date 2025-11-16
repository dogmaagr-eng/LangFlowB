"""add project tables

Revision ID: f9a1b2c3d4e5
Revises: fd531f8868b1_fix_credential_table.py
Create Date: 2025-11-16 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f9a1b2c3d4e5"
down_revision: str | Sequence[str] | None = "fd531f8868b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)  # type: ignore
    existing_tables = inspector.get_table_names()

    if "project" not in existing_tables:
        op.create_table(
            "project",
            sa.Column("id", sqlmodel.sql.sqltypes.types.Uuid(), nullable=False),
            sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("owner_id", sqlmodel.sql.sqltypes.types.Uuid(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["owner_id"], ["user.id"], name="fk_project_owner_id_user"),
            sa.PrimaryKeyConstraint("id", name="pk_project"),
            sa.UniqueConstraint("id", name="uq_project_id"),
        )

    if "context" not in existing_tables:
        op.create_table(
            "context",
            sa.Column("id", sqlmodel.sql.sqltypes.types.Uuid(), nullable=False),
            sa.Column("project_id", sqlmodel.sql.sqltypes.types.Uuid(), nullable=False),
            sa.Column("key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("value", sa.JSON(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["project_id"], ["project.id"], name="fk_context_project_id_project"),
            sa.PrimaryKeyConstraint("id", name="pk_context"),
            sa.UniqueConstraint("id", name="uq_context_id"),
        )

    if "orchestrationrun" not in existing_tables:
        op.create_table(
            "orchestrationrun",
            sa.Column("id", sqlmodel.sql.sqltypes.types.Uuid(), nullable=False),
            sa.Column("project_id", sqlmodel.sql.sqltypes.types.Uuid(), nullable=True),
            sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column("steps", sa.JSON(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["project_id"], ["project.id"], name="fk_orch_project_id_project"),
            sa.PrimaryKeyConstraint("id", name="pk_orchestrationrun"),
            sa.UniqueConstraint("id", name="uq_orchestrationrun_id"),
        )

    if "generatedartifact" not in existing_tables:
        op.create_table(
            "generatedartifact",
            sa.Column("id", sqlmodel.sql.sqltypes.types.Uuid(), nullable=False),
            sa.Column("project_id", sqlmodel.sql.sqltypes.types.Uuid(), nullable=True),
            sa.Column("run_id", sqlmodel.sql.sqltypes.types.Uuid(), nullable=True),
            sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("path", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
            sa.Column("content", sa.JSON(), nullable=True),
            sa.Column("metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["project_id"], ["project.id"], name="fk_artifact_project_id_project"),
            sa.ForeignKeyConstraint(["run_id"], ["orchestrationrun.id"], name="fk_artifact_run_id_orch"),
            sa.PrimaryKeyConstraint("id", name="pk_generatedartifact"),
            sa.UniqueConstraint("id", name="uq_generatedartifact_id"),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)  # type: ignore
    existing_tables = inspector.get_table_names()

    if "generatedartifact" in existing_tables:
        op.drop_table("generatedartifact")
    if "orchestrationrun" in existing_tables:
        op.drop_table("orchestrationrun")
    if "context" in existing_tables:
        op.drop_table("context")
    if "project" in existing_tables:
        op.drop_table("project")
