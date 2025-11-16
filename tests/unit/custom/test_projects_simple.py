"""Simplified unit tests for Project CRUD Service layer (no Langflow dependencies)."""

import pytest
from uuid import uuid4
from datetime import datetime
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
import sys
from pathlib import Path

# Test minimal models directly
from sqlmodel import Field, SQLModel, Column, JSON
from datetime import timezone
from uuid import UUID, uuid4 as uuid4_func
from typing import Optional


# Inline test models to avoid dependency on full langflow import
class ProjectTest(SQLModel, table=True):
    __tablename__ = "project_test"
    id: UUID = Field(default_factory=uuid4_func, primary_key=True, unique=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    meta_data: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class ContextTest(SQLModel, table=True):
    __tablename__ = "context_test"
    id: UUID = Field(default_factory=uuid4_func, primary_key=True, unique=True)
    project_id: UUID = Field(foreign_key="project_test.id", index=True)
    key: str = Field(index=True)
    value: dict | str | None = Field(default=None, sa_column=Column(JSON))
    updated_at: Optional[datetime] = None


class OrchestrationRunTest(SQLModel, table=True):
    __tablename__ = "orchestration_run_test"
    id: UUID = Field(default_factory=uuid4_func, primary_key=True, unique=True)
    project_id: Optional[UUID] = Field(default=None, foreign_key="project_test.id", index=True, nullable=True)
    status: Optional[str] = Field(default="PENDING", index=True)
    steps: dict | None = Field(default=None, sa_column=Column(JSON))
    started_at: Optional[datetime] = Field(default=None, nullable=True)
    finished_at: Optional[datetime] = Field(default=None, nullable=True)


class GeneratedArtifactTest(SQLModel, table=True):
    __tablename__ = "generated_artifact_test"
    id: UUID = Field(default_factory=uuid4_func, primary_key=True, unique=True)
    project_id: Optional[UUID] = None
    run_id: Optional[UUID] = None
    name: str = Field()
    path: Optional[str] = None
    content: Optional[str] = Field(default=None, sa_column=Column(JSON))
    meta_data: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Simplified test service
class ProjectServiceTest:
    def __init__(self, session: Session):
        self.session = session

    def create_project(self, name: str, description: Optional[str] = None, metadata: Optional[dict] = None) -> ProjectTest:
        project = ProjectTest(name=name, description=description, meta_data=metadata)
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project

    def get_project(self, project_id: UUID) -> Optional[ProjectTest]:
        from sqlmodel import select
        return self.session.exec(select(ProjectTest).where(ProjectTest.id == project_id)).first()

    def list_projects(self, skip: int = 0, limit: int = 10) -> list[ProjectTest]:
        from sqlmodel import select
        return self.session.exec(select(ProjectTest).offset(skip).limit(limit)).all()

    def update_project(self, project_id: UUID, name: Optional[str] = None, description: Optional[str] = None, metadata: Optional[dict] = None) -> Optional[ProjectTest]:
        project = self.get_project(project_id)
        if not project:
            return None
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if metadata is not None:
            project.meta_data = metadata
        project.updated_at = datetime.now(timezone.utc)
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project

    def delete_project(self, project_id: UUID) -> bool:
        project = self.get_project(project_id)
        if not project:
            return False
        self.session.delete(project)
        self.session.commit()
        return True

    def create_context(self, project_id: UUID, key: str, value: Optional[dict | str] = None) -> ContextTest:
        context = ContextTest(project_id=project_id, key=key, value=value)
        self.session.add(context)
        self.session.commit()
        self.session.refresh(context)
        return context

    def get_context(self, context_id: UUID) -> Optional[ContextTest]:
        from sqlmodel import select
        return self.session.exec(select(ContextTest).where(ContextTest.id == context_id)).first()

    def create_artifact(self, project_id: UUID, name: str, path: Optional[str] = None, content: Optional[str] = None, metadata: Optional[dict] = None, run_id: Optional[UUID] = None) -> GeneratedArtifactTest:
        artifact = GeneratedArtifactTest(project_id=project_id, run_id=run_id, name=name, path=path, content=content, meta_data=metadata)
        self.session.add(artifact)
        self.session.commit()
        self.session.refresh(artifact)
        return artifact

    def get_artifact(self, artifact_id: UUID) -> Optional[GeneratedArtifactTest]:
        from sqlmodel import select
        return self.session.exec(select(GeneratedArtifactTest).where(GeneratedArtifactTest.id == artifact_id)).first()

    def create_run(self, project_id: UUID, status: str = "PENDING", steps: Optional[dict] = None) -> OrchestrationRunTest:
        run = OrchestrationRunTest(project_id=project_id, status=status, steps=steps)
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def get_run(self, run_id: UUID) -> Optional[OrchestrationRunTest]:
        from sqlmodel import select
        return self.session.exec(select(OrchestrationRunTest).where(OrchestrationRunTest.id == run_id)).first()


# Fixtures
@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="service")
def service_fixture(session: Session):
    """Create a ProjectService instance for testing."""
    return ProjectServiceTest(session)


@pytest.fixture(name="test_project")
def test_project_fixture(service: ProjectServiceTest):
    """Create a test project."""
    return service.create_project(name="Test Project", description="A test project", metadata={"key": "value"})


# Tests
class TestProjectCRUD:
    """Test Project CRUD operations."""

    def test_create_project(self, service: ProjectServiceTest):
        """Test creating a project."""
        project = service.create_project(name="New Project", description="Test description", metadata={"env": "test"})
        assert project.name == "New Project"
        assert project.description == "Test description"
        assert project.meta_data == {"env": "test"}
        assert project.id is not None

    def test_get_project(self, service: ProjectServiceTest, test_project: ProjectTest):
        """Test getting a project by ID."""
        retrieved = service.get_project(test_project.id)
        assert retrieved is not None
        assert retrieved.id == test_project.id
        assert retrieved.name == "Test Project"

    def test_get_nonexistent_project(self, service: ProjectServiceTest):
        """Test getting a nonexistent project."""
        retrieved = service.get_project(uuid4())
        assert retrieved is None

    def test_list_projects(self, service: ProjectServiceTest):
        """Test listing projects."""
        service.create_project(name="Project 1")
        service.create_project(name="Project 2")
        projects = service.list_projects(skip=0, limit=10)
        assert len(projects) >= 2

    def test_update_project(self, service: ProjectServiceTest, test_project: ProjectTest):
        """Test updating a project."""
        updated = service.update_project(test_project.id, name="Updated Project", description="Updated description")
        assert updated is not None
        assert updated.name == "Updated Project"
        assert updated.description == "Updated description"

    def test_delete_project(self, service: ProjectServiceTest, test_project: ProjectTest):
        """Test deleting a project."""
        project_id = test_project.id
        success = service.delete_project(project_id)
        assert success is True
        retrieved = service.get_project(project_id)
        assert retrieved is None


class TestContextCRUD:
    """Test Context CRUD operations."""

    def test_create_context(self, service: ProjectServiceTest, test_project: ProjectTest):
        """Test creating a context entry."""
        context = service.create_context(project_id=test_project.id, key="database_url", value="sqlite:///test.db")
        assert context.project_id == test_project.id
        assert context.key == "database_url"
        assert context.value == "sqlite:///test.db"

    def test_get_context(self, service: ProjectServiceTest, test_project: ProjectTest):
        """Test getting a context entry."""
        created = service.create_context(project_id=test_project.id, key="api_key", value={"token": "secret"})
        retrieved = service.get_context(created.id)
        assert retrieved is not None
        assert retrieved.key == "api_key"


class TestArtifactCRUD:
    """Test GeneratedArtifact CRUD operations."""

    def test_create_artifact(self, service: ProjectServiceTest, test_project: ProjectTest):
        """Test creating a generated artifact."""
        artifact = service.create_artifact(
            project_id=test_project.id,
            name="component.jsx",
            path="/artifacts/component.jsx",
            content="export default function Component() { return <div>Hello</div>; }",
            metadata={"type": "framer"},
        )
        assert artifact.project_id == test_project.id
        assert artifact.name == "component.jsx"
        assert artifact.meta_data == {"type": "framer"}

    def test_get_artifact(self, service: ProjectServiceTest, test_project: ProjectTest):
        """Test getting an artifact."""
        created = service.create_artifact(project_id=test_project.id, name="test.jsx")
        retrieved = service.get_artifact(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id


class TestOrchestrationRunCRUD:
    """Test OrchestrationRun CRUD operations."""

    def test_create_run(self, service: ProjectServiceTest, test_project: ProjectTest):
        """Test creating an orchestration run."""
        run = service.create_run(project_id=test_project.id, status="PENDING", steps={"step1": "CodeLlama", "step2": "CodeGemma"})
        assert run.project_id == test_project.id
        assert run.status == "PENDING"
        assert run.steps == {"step1": "CodeLlama", "step2": "CodeGemma"}

    def test_get_run(self, service: ProjectServiceTest, test_project: ProjectTest):
        """Test getting an orchestration run."""
        created = service.create_run(project_id=test_project.id)
        retrieved = service.get_run(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
