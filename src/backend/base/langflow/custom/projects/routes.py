"""FastAPI router for Project/Context/OrchestrationRun/GeneratedArtifact CRUD operations."""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from langflow.services.database.service import get_session
from langflow.custom.projects.service import ProjectService
from langflow.custom.projects.schemas import (
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    ContextCreate,
    ContextRead,
    ContextUpdate,
    OrchestrationRunCreate,
    OrchestrationRunRead,
    OrchestrationRunUpdate,
    GeneratedArtifactCreate,
    GeneratedArtifactRead,
    GeneratedArtifactUpdate,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service(session: Session = Depends(get_session)) -> ProjectService:
    """Dependency injection for ProjectService."""
    return ProjectService(session)


# ============ PROJECT ENDPOINTS ============


@router.post("/", response_model=ProjectRead, status_code=201)
def create_project(
    project: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    """Create a new project."""
    created = service.create_project(
        name=project.name,
        description=project.description,
        metadata=project.metadata,
    )
    return ProjectRead.model_validate(created)


@router.get("/", response_model=list[ProjectRead])
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    service: ProjectService = Depends(get_project_service),
) -> list[ProjectRead]:
    """List all projects with pagination."""
    projects = service.list_projects(skip=skip, limit=limit)
    return [ProjectRead.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    """Get a project by ID."""
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRead.model_validate(project)


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: UUID,
    project_update: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    """Update a project."""
    updated = service.update_project(
        project_id=project_id,
        name=project_update.name,
        description=project_update.description,
        metadata=project_update.metadata,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRead.model_validate(updated)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> None:
    """Delete a project (cascades to related data)."""
    success = service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")


# ============ CONTEXT ENDPOINTS ============


@router.post("/{project_id}/context", response_model=ContextRead, status_code=201)
def create_context(
    project_id: UUID,
    context: ContextCreate,
    service: ProjectService = Depends(get_project_service),
) -> ContextRead:
    """Create a context entry for a project."""
    # Verify project exists
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    created = service.create_context(
        project_id=project_id,
        key=context.key,
        value=context.value,
    )
    return ContextRead.model_validate(created)


@router.get("/{project_id}/context", response_model=list[ContextRead])
def list_context(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: ProjectService = Depends(get_project_service),
) -> list[ContextRead]:
    """List all context entries for a project."""
    # Verify project exists
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    contexts = service.list_context_by_project(project_id, skip=skip, limit=limit)
    return [ContextRead.model_validate(c) for c in contexts]


@router.get("/context/{context_id}", response_model=ContextRead)
def get_context(
    context_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> ContextRead:
    """Get a context entry by ID."""
    context = service.get_context(context_id)
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    return ContextRead.model_validate(context)


@router.put("/context/{context_id}", response_model=ContextRead)
def update_context(
    context_id: UUID,
    context_update: ContextUpdate,
    service: ProjectService = Depends(get_project_service),
) -> ContextRead:
    """Update a context entry."""
    updated = service.update_context(
        context_id=context_id,
        key=context_update.key,
        value=context_update.value,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Context not found")
    return ContextRead.model_validate(updated)


@router.delete("/context/{context_id}", status_code=204)
def delete_context(
    context_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> None:
    """Delete a context entry."""
    success = service.delete_context(context_id)
    if not success:
        raise HTTPException(status_code=404, detail="Context not found")


# ============ ORCHESTRATION RUN ENDPOINTS ============


@router.post("/{project_id}/runs", response_model=OrchestrationRunRead, status_code=201)
def create_run(
    project_id: UUID,
    run: OrchestrationRunCreate,
    service: ProjectService = Depends(get_project_service),
) -> OrchestrationRunRead:
    """Create an orchestration run for a project."""
    # Verify project exists
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    created = service.create_run(
        project_id=project_id,
        status=run.status,
        steps=run.steps,
    )
    return OrchestrationRunRead.model_validate(created)


@router.get("/{project_id}/runs", response_model=list[OrchestrationRunRead])
def list_runs(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: ProjectService = Depends(get_project_service),
) -> list[OrchestrationRunRead]:
    """List all orchestration runs for a project."""
    # Verify project exists
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    runs = service.list_runs_by_project(project_id, skip=skip, limit=limit)
    return [OrchestrationRunRead.model_validate(r) for r in runs]


@router.get("/runs/{run_id}", response_model=OrchestrationRunRead)
def get_run(
    run_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> OrchestrationRunRead:
    """Get an orchestration run by ID."""
    run = service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Orchestration run not found")
    return OrchestrationRunRead.model_validate(run)


@router.put("/runs/{run_id}", response_model=OrchestrationRunRead)
def update_run(
    run_id: UUID,
    run_update: OrchestrationRunUpdate,
    service: ProjectService = Depends(get_project_service),
) -> OrchestrationRunRead:
    """Update an orchestration run."""
    updated = service.update_run_status(
        run_id=run_id,
        status=run_update.status or "PENDING",
        finished=run_update.finished or False,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Orchestration run not found")
    return OrchestrationRunRead.model_validate(updated)


@router.delete("/runs/{run_id}", status_code=204)
def delete_run(
    run_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> None:
    """Delete an orchestration run (cascades to artifacts)."""
    success = service.delete_run(run_id)
    if not success:
        raise HTTPException(status_code=404, detail="Orchestration run not found")


# ============ GENERATED ARTIFACT ENDPOINTS ============


@router.post("/{project_id}/artifacts", response_model=GeneratedArtifactRead, status_code=201)
def create_artifact(
    project_id: UUID,
    artifact: GeneratedArtifactCreate,
    service: ProjectService = Depends(get_project_service),
) -> GeneratedArtifactRead:
    """Create a generated artifact for a project."""
    # Verify project exists
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    created = service.create_artifact(
        project_id=project_id,
        name=artifact.name,
        path=artifact.path,
        content=artifact.content,
        metadata=artifact.metadata,
        run_id=artifact.run_id,
    )
    return GeneratedArtifactRead.model_validate(created)


@router.get("/{project_id}/artifacts", response_model=list[GeneratedArtifactRead])
def list_artifacts_by_project(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: ProjectService = Depends(get_project_service),
) -> list[GeneratedArtifactRead]:
    """List all artifacts for a project."""
    # Verify project exists
    if not service.get_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")

    artifacts = service.list_artifacts_by_project(project_id, skip=skip, limit=limit)
    return [GeneratedArtifactRead.model_validate(a) for a in artifacts]


@router.get("/runs/{run_id}/artifacts", response_model=list[GeneratedArtifactRead])
def list_artifacts_by_run(
    run_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: ProjectService = Depends(get_project_service),
) -> list[GeneratedArtifactRead]:
    """List all artifacts for an orchestration run."""
    # Verify run exists
    if not service.get_run(run_id):
        raise HTTPException(status_code=404, detail="Orchestration run not found")

    artifacts = service.list_artifacts_by_run(run_id, skip=skip, limit=limit)
    return [GeneratedArtifactRead.model_validate(a) for a in artifacts]


@router.get("/artifacts/{artifact_id}", response_model=GeneratedArtifactRead)
def get_artifact(
    artifact_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> GeneratedArtifactRead:
    """Get an artifact by ID."""
    artifact = service.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return GeneratedArtifactRead.model_validate(artifact)


@router.put("/artifacts/{artifact_id}", response_model=GeneratedArtifactRead)
def update_artifact(
    artifact_id: UUID,
    artifact_update: GeneratedArtifactUpdate,
    service: ProjectService = Depends(get_project_service),
) -> GeneratedArtifactRead:
    """Update an artifact."""
    updated = service.update_artifact(
        artifact_id=artifact_id,
        name=artifact_update.name,
        path=artifact_update.path,
        content=artifact_update.content,
        metadata=artifact_update.metadata,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return GeneratedArtifactRead.model_validate(updated)


@router.delete("/artifacts/{artifact_id}", status_code=204)
def delete_artifact(
    artifact_id: UUID,
    service: ProjectService = Depends(get_project_service),
) -> None:
    """Delete an artifact."""
    success = service.delete_artifact(artifact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Artifact not found")
