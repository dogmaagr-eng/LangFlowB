"""Pydantic schemas for Orchestrator API."""

from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class StepInputSchema(BaseModel):
    """Schema for orchestration step input."""
    step_name: str = Field(..., min_length=1, max_length=255)
    model_type: str = Field(..., description="CodeLlama, CodeGemma, T5Gemma")
    prompt: str = Field(..., min_length=10, max_length=10000)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PipelineCreateSchema(BaseModel):
    """Schema for creating an orchestration pipeline."""
    project_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    steps: List[StepInputSchema] = Field(..., min_items=1, max_items=10)
    global_context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ArtifactSchema(BaseModel):
    """Schema for generated artifact."""
    type: str
    name: str
    content: str


class StepOutputSchema(BaseModel):
    """Schema for orchestration step output."""
    step_name: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    artifacts: List[ArtifactSchema] = Field(default_factory=list)
    execution_time: float


class PipelineExecutionSchema(BaseModel):
    """Schema for pipeline execution result."""
    run_id: str
    project_id: str
    status: str
    steps: List[StepOutputSchema] = Field(default_factory=list)
    final_artifacts: List[ArtifactSchema] = Field(default_factory=list)
    assembled_code: Optional[str] = None
    started_at: str
    finished_at: str
    error: Optional[str] = None

    class Config:
        from_attributes = True


class ExecutionSummarySchema(BaseModel):
    """Schema for execution summary."""
    run_id: str
    total_steps: int
    successful_steps: int
    failed_steps: int
    total_execution_time: float
    steps: List[StepOutputSchema] = Field(default_factory=list)

    class Config:
        from_attributes = True
