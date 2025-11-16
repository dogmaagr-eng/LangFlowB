from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import JSON, Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from langflow.services.database.models.user.model import User


class ProjectBase(SQLModel):
    name: str = Field(index=True)
    description: str | None = Field(default=None)
    metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=True)


class Project(ProjectBase, table=True):  # type: ignore[call-arg]
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    owner_id: UUID | None = Field(default=None, foreign_key="user.id", index=True, nullable=True)
    owner: "User" | None = Relationship(back_populates="projects")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Context(SQLModel, table=True):  # type: ignore[call-arg]
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    project_id: UUID = Field(foreign_key="project.id", index=True)
    key: str = Field(index=True)
    value: dict | str | None = Field(default=None, sa_column=Column(JSON))
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=True)


class OrchestrationRun(SQLModel, table=True):  # type: ignore[call-arg]
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    project_id: UUID | None = Field(default=None, foreign_key="project.id", index=True, nullable=True)
    status: str | None = Field(default="PENDING", index=True)
    steps: dict | None = Field(default=None, sa_column=Column(JSON))
    started_at: datetime | None = Field(default=None, nullable=True)
    finished_at: datetime | None = Field(default=None, nullable=True)


class GeneratedArtifact(SQLModel, table=True):  # type: ignore[call-arg]
    id: UUID = Field(default_factory=uuid4, primary_key=True, unique=True)
    project_id: UUID | None = Field(default=None, foreign_key="project.id", index=True, nullable=True)
    run_id: UUID | None = Field(default=None, foreign_key="orchestrationrun.id", index=True, nullable=True)
    name: str = Field()
    path: str | None = Field(default=None, nullable=True)
    content: str | None = Field(default=None, sa_column=Column(JSON), nullable=True)
    metadata: dict | None = Field(default=None, sa_column=Column(JSON), nullable=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: UUID
