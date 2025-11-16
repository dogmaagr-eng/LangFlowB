"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ============ PROJECT SCHEMAS ============

class ProjectCreate(BaseModel):
    """Schema for creating a project."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[dict] = Field(None)


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[dict] = Field(None)


class ProjectRead(BaseModel):
    """Schema for reading a project."""
    id: UUID
    name: str
    description: Optional[str]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============ CONTEXT SCHEMAS ============

class ContextCreate(BaseModel):
    """Schema for creating a context entry."""
    key: str = Field(..., min_length=1, max_length=255)
    value: Optional[dict | str] = Field(None)


class ContextUpdate(BaseModel):
    """Schema for updating a context entry."""
    key: Optional[str] = Field(None, min_length=1, max_length=255)
    value: Optional[dict | str] = Field(None)


class ContextRead(BaseModel):
    """Schema for reading a context entry."""
    id: UUID
    project_id: UUID
    key: str
    value: Optional[dict | str]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============ ORCHESTRATION RUN SCHEMAS ============

class OrchestrationRunCreate(BaseModel):
    """Schema for creating an orchestration run."""
    status: Optional[str] = Field("PENDING", max_length=50)
    steps: Optional[dict] = Field(None)


class OrchestrationRunUpdate(BaseModel):
    """Schema for updating an orchestration run."""
    status: Optional[str] = Field(None, max_length=50)
    finished: Optional[bool] = Field(False)


class OrchestrationRunRead(BaseModel):
    """Schema for reading an orchestration run."""
    id: UUID
    project_id: UUID
    status: str
    steps: Optional[dict]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============ GENERATED ARTIFACT SCHEMAS ============

class GeneratedArtifactCreate(BaseModel):
    """Schema for creating a generated artifact."""
    name: str = Field(..., min_length=1, max_length=255)
    path: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None)
    metadata: Optional[dict] = Field(None)
    run_id: Optional[UUID] = Field(None)


class GeneratedArtifactUpdate(BaseModel):
    """Schema for updating a generated artifact."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    path: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = Field(None)
    metadata: Optional[dict] = Field(None)


class GeneratedArtifactRead(BaseModel):
    """Schema for reading a generated artifact."""
    id: UUID
    project_id: UUID
    run_id: Optional[UUID]
    name: str
    path: Optional[str]
    content: Optional[str]
    metadata: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True
