"""Service layer for project management (CRUD operations)."""

from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from langflow.services.database.models.project.model import (
    Project,
    Context,
    OrchestrationRun,
    GeneratedArtifact,
)


class ProjectService:
    """Service for managing projects."""

    def __init__(self, session: Session):
        self.session = session

    # ============ PROJECT CRUD ============

    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        owner_id: Optional[UUID] = None,
    ) -> Project:
        """Create a new project."""
        project = Project(
            name=name,
            description=description,
            metadata=metadata,
            owner_id=owner_id,
        )
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project

    def get_project(self, project_id: UUID) -> Optional[Project]:
        """Get a project by ID."""
        return self.session.exec(
            select(Project).where(Project.id == project_id)
        ).first()

    def list_projects(self, skip: int = 0, limit: int = 10) -> list[Project]:
        """List all projects with pagination."""
        return self.session.exec(
            select(Project).offset(skip).limit(limit)
        ).all()

    def update_project(
        self,
        project_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[Project]:
        """Update a project."""
        project = self.get_project(project_id)
        if not project:
            return None

        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if metadata is not None:
            project.metadata = metadata
        project.updated_at = datetime.now(timezone.utc)

        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project

    def delete_project(self, project_id: UUID) -> bool:
        """Delete a project (and cascade related data)."""
        project = self.get_project(project_id)
        if not project:
            return False

        # Delete cascade
        self.session.exec(
            select(Context).where(Context.project_id == project_id)
        ).delete(synchronize_session=False)
        self.session.exec(
            select(OrchestrationRun).where(OrchestrationRun.project_id == project_id)
        ).delete(synchronize_session=False)
        self.session.exec(
            select(GeneratedArtifact).where(
                GeneratedArtifact.project_id == project_id
            )
        ).delete(synchronize_session=False)

        self.session.delete(project)
        self.session.commit()
        return True

    # ============ CONTEXT CRUD ============

    def create_context(
        self,
        project_id: UUID,
        key: str,
        value: Optional[dict | str] = None,
    ) -> Context:
        """Create a context entry for a project."""
        context = Context(
            project_id=project_id,
            key=key,
            value=value,
        )
        self.session.add(context)
        self.session.commit()
        self.session.refresh(context)
        return context

    def get_context(self, context_id: UUID) -> Optional[Context]:
        """Get a context by ID."""
        return self.session.exec(
            select(Context).where(Context.id == context_id)
        ).first()

    def list_context_by_project(
        self, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Context]:
        """List all context entries for a project."""
        return self.session.exec(
            select(Context)
            .where(Context.project_id == project_id)
            .offset(skip)
            .limit(limit)
        ).all()

    def update_context(
        self,
        context_id: UUID,
        key: Optional[str] = None,
        value: Optional[dict | str] = None,
    ) -> Optional[Context]:
        """Update a context entry."""
        context = self.get_context(context_id)
        if not context:
            return None

        if key is not None:
            context.key = key
        if value is not None:
            context.value = value
        context.updated_at = datetime.now(timezone.utc)

        self.session.add(context)
        self.session.commit()
        self.session.refresh(context)
        return context

    def delete_context(self, context_id: UUID) -> bool:
        """Delete a context entry."""
        context = self.get_context(context_id)
        if not context:
            return False

        self.session.delete(context)
        self.session.commit()
        return True

    # ============ ORCHESTRATION RUN CRUD ============

    def create_run(
        self,
        project_id: UUID,
        status: str = "PENDING",
        steps: Optional[dict] = None,
    ) -> OrchestrationRun:
        """Create an orchestration run."""
        run = OrchestrationRun(
            project_id=project_id,
            status=status,
            steps=steps,
            started_at=datetime.now(timezone.utc) if status == "RUNNING" else None,
        )
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def get_run(self, run_id: UUID) -> Optional[OrchestrationRun]:
        """Get an orchestration run by ID."""
        return self.session.exec(
            select(OrchestrationRun).where(OrchestrationRun.id == run_id)
        ).first()

    def list_runs_by_project(
        self, project_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[OrchestrationRun]:
        """List all orchestration runs for a project."""
        return self.session.exec(
            select(OrchestrationRun)
            .where(OrchestrationRun.project_id == project_id)
            .offset(skip)
            .limit(limit)
        ).all()

    def update_run_status(
        self, run_id: UUID, status: str, finished: bool = False
    ) -> Optional[OrchestrationRun]:
        """Update the status of an orchestration run."""
        run = self.get_run(run_id)
        if not run:
            return None

        run.status = status
        if finished:
            run.finished_at = datetime.now(timezone.utc)

        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def delete_run(self, run_id: UUID) -> bool:
        """Delete an orchestration run and its artifacts."""
        run = self.get_run(run_id)
        if not run:
            return False

        # Delete artifacts related to this run
        self.session.exec(
            select(GeneratedArtifact).where(GeneratedArtifact.run_id == run_id)
        ).delete(synchronize_session=False)

        self.session.delete(run)
        self.session.commit()
        return True

    # ============ GENERATED ARTIFACT CRUD ============

    def create_artifact(
        self,
        project_id: UUID,
        name: str,
        path: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[dict] = None,
        run_id: Optional[UUID] = None,
    ) -> GeneratedArtifact:
        """Create a generated artifact."""
        artifact = GeneratedArtifact(
            project_id=project_id,
            run_id=run_id,
            name=name,
            path=path,
            content=content,
            metadata=metadata,
        )
        self.session.add(artifact)
        self.session.commit()
        self.session.refresh(artifact)
        return artifact

    def get_artifact(self, artifact_id: UUID) -> Optional[GeneratedArtifact]:
        """Get an artifact by ID."""
        return self.session.exec(
            select(GeneratedArtifact).where(GeneratedArtifact.id == artifact_id)
        ).first()

    def list_artifacts_by_project(
        self, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[GeneratedArtifact]:
        """List all artifacts for a project."""
        return self.session.exec(
            select(GeneratedArtifact)
            .where(GeneratedArtifact.project_id == project_id)
            .offset(skip)
            .limit(limit)
        ).all()

    def list_artifacts_by_run(
        self, run_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[GeneratedArtifact]:
        """List all artifacts for an orchestration run."""
        return self.session.exec(
            select(GeneratedArtifact)
            .where(GeneratedArtifact.run_id == run_id)
            .offset(skip)
            .limit(limit)
        ).all()

    def update_artifact(
        self,
        artifact_id: UUID,
        name: Optional[str] = None,
        path: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[GeneratedArtifact]:
        """Update an artifact."""
        artifact = self.get_artifact(artifact_id)
        if not artifact:
            return None

        if name is not None:
            artifact.name = name
        if path is not None:
            artifact.path = path
        if content is not None:
            artifact.content = content
        if metadata is not None:
            artifact.metadata = metadata

        self.session.add(artifact)
        self.session.commit()
        self.session.refresh(artifact)
        return artifact

    def delete_artifact(self, artifact_id: UUID) -> bool:
        """Delete an artifact."""
        artifact = self.get_artifact(artifact_id)
        if not artifact:
            return False

        self.session.delete(artifact)
        self.session.commit()
        return True
