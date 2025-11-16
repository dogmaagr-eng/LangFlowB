"""Unit tests for Project CRUD operations."""

import pytest
from uuid import uuid4
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
import sys
from pathlib import Path

# Add the langflow package to the path for imports
repo_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "src" / "backend" / "base"))
sys.path.insert(0, str(repo_root / "src"))

from langflow.services.database.models.project.model import (
    Project,
    Context,
    OrchestrationRun,
    GeneratedArtifact,
)
from langflow.custom.projects.service import ProjectService


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
    return ProjectService(session)


@pytest.fixture(name="test_project")
def test_project_fixture(service: ProjectService):
    """Create a test project."""
    return service.create_project(
        name="Test Project",
        description="A test project",
        metadata={"key": "value"},
    )


class TestProjectCRUD:
    """Test Project CRUD operations."""

    def test_create_project(self, service: ProjectService):
        """Test creating a project."""
        project = service.create_project(
            name="New Project",
            description="Test description",
            metadata={"env": "test"},
        )
        assert project.name == "New Project"
        assert project.description == "Test description"
        assert project.metadata == {"env": "test"}
        assert project.id is not None

    def test_get_project(self, service: ProjectService, test_project: Project):
        """Test getting a project by ID."""
        retrieved = service.get_project(test_project.id)
        assert retrieved is not None
        assert retrieved.id == test_project.id
        assert retrieved.name == "Test Project"

    def test_get_nonexistent_project(self, service: ProjectService):
        """Test getting a nonexistent project."""
        retrieved = service.get_project(uuid4())
        assert retrieved is None

    def test_list_projects(self, service: ProjectService):
        """Test listing projects."""
        service.create_project(name="Project 1")
        service.create_project(name="Project 2")
        projects = service.list_projects(skip=0, limit=10)
        assert len(projects) >= 2

    def test_update_project(self, service: ProjectService, test_project: Project):
        """Test updating a project."""
        updated = service.update_project(
            test_project.id,
            name="Updated Project",
            description="Updated description",
        )
        assert updated is not None
        assert updated.name == "Updated Project"
        assert updated.description == "Updated description"

    def test_delete_project(self, service: ProjectService, test_project: Project):
        """Test deleting a project."""
        project_id = test_project.id
        success = service.delete_project(project_id)
        assert success is True
        retrieved = service.get_project(project_id)
        assert retrieved is None


class TestContextCRUD:
    """Test Context CRUD operations."""

    def test_create_context(self, service: ProjectService, test_project: Project):
        """Test creating a context entry."""
        context = service.create_context(
            project_id=test_project.id,
            key="database_url",
            value="sqlite:///test.db",
        )
        assert context.project_id == test_project.id
        assert context.key == "database_url"
        assert context.value == "sqlite:///test.db"

    def test_get_context(self, service: ProjectService, test_project: Project):
        """Test getting a context entry."""
        created = service.create_context(
            project_id=test_project.id,
            key="api_key",
            value={"token": "secret"},
        )
        retrieved = service.get_context(created.id)
        assert retrieved is not None
        assert retrieved.key == "api_key"

    def test_list_context_by_project(
        self, service: ProjectService, test_project: Project
    ):
        """Test listing context entries for a project."""
        service.create_context(project_id=test_project.id, key="key1", value="val1")
        service.create_context(project_id=test_project.id, key="key2", value="val2")
        contexts = service.list_context_by_project(test_project.id)
        assert len(contexts) >= 2

    def test_update_context(self, service: ProjectService, test_project: Project):
        """Test updating a context entry."""
        context = service.create_context(
            project_id=test_project.id, key="old_key", value="old_value"
        )
        updated = service.update_context(
            context.id, key="new_key", value="new_value"
        )
        assert updated is not None
        assert updated.key == "new_key"
        assert updated.value == "new_value"

    def test_delete_context(self, service: ProjectService, test_project: Project):
        """Test deleting a context entry."""
        context = service.create_context(
            project_id=test_project.id, key="key", value="value"
        )
        success = service.delete_context(context.id)
        assert success is True
        retrieved = service.get_context(context.id)
        assert retrieved is None


class TestOrchestrationRunCRUD:
    """Test OrchestrationRun CRUD operations."""

    def test_create_run(self, service: ProjectService, test_project: Project):
        """Test creating an orchestration run."""
        run = service.create_run(
            project_id=test_project.id,
            status="PENDING",
            steps={"step1": "CodeLlama", "step2": "CodeGemma"},
        )
        assert run.project_id == test_project.id
        assert run.status == "PENDING"
        assert run.steps == {"step1": "CodeLlama", "step2": "CodeGemma"}

    def test_get_run(self, service: ProjectService, test_project: Project):
        """Test getting an orchestration run."""
        created = service.create_run(project_id=test_project.id)
        retrieved = service.get_run(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_list_runs_by_project(self, service: ProjectService, test_project: Project):
        """Test listing orchestration runs for a project."""
        service.create_run(project_id=test_project.id)
        service.create_run(project_id=test_project.id)
        runs = service.list_runs_by_project(test_project.id)
        assert len(runs) >= 2

    def test_update_run_status(self, service: ProjectService, test_project: Project):
        """Test updating the status of an orchestration run."""
        run = service.create_run(project_id=test_project.id)
        updated = service.update_run_status(run.id, status="RUNNING")
        assert updated is not None
        assert updated.status == "RUNNING"

    def test_delete_run(self, service: ProjectService, test_project: Project):
        """Test deleting an orchestration run."""
        run = service.create_run(project_id=test_project.id)
        run_id = run.id
        success = service.delete_run(run_id)
        assert success is True
        retrieved = service.get_run(run_id)
        assert retrieved is None


class TestGeneratedArtifactCRUD:
    """Test GeneratedArtifact CRUD operations."""

    def test_create_artifact(self, service: ProjectService, test_project: Project):
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
        assert artifact.metadata == {"type": "framer"}

    def test_get_artifact(self, service: ProjectService, test_project: Project):
        """Test getting an artifact."""
        created = service.create_artifact(
            project_id=test_project.id, name="test.jsx"
        )
        retrieved = service.get_artifact(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_list_artifacts_by_project(
        self, service: ProjectService, test_project: Project
    ):
        """Test listing artifacts for a project."""
        service.create_artifact(project_id=test_project.id, name="artifact1.jsx")
        service.create_artifact(project_id=test_project.id, name="artifact2.jsx")
        artifacts = service.list_artifacts_by_project(test_project.id)
        assert len(artifacts) >= 2

    def test_list_artifacts_by_run(
        self, service: ProjectService, test_project: Project
    ):
        """Test listing artifacts for a specific run."""
        run = service.create_run(project_id=test_project.id)
        service.create_artifact(
            project_id=test_project.id, run_id=run.id, name="artifact1.jsx"
        )
        service.create_artifact(
            project_id=test_project.id, run_id=run.id, name="artifact2.jsx"
        )
        artifacts = service.list_artifacts_by_run(run.id)
        assert len(artifacts) == 2

    def test_update_artifact(self, service: ProjectService, test_project: Project):
        """Test updating an artifact."""
        artifact = service.create_artifact(
            project_id=test_project.id, name="old.jsx", content="old content"
        )
        updated = service.update_artifact(
            artifact.id, name="new.jsx", content="new content"
        )
        assert updated is not None
        assert updated.name == "new.jsx"
        assert updated.content == "new content"

    def test_delete_artifact(self, service: ProjectService, test_project: Project):
        """Test deleting an artifact."""
        artifact = service.create_artifact(
            project_id=test_project.id, name="test.jsx"
        )
        artifact_id = artifact.id
        success = service.delete_artifact(artifact_id)
        assert success is True
        retrieved = service.get_artifact(artifact_id)
        assert retrieved is None
