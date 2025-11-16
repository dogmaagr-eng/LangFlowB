"""FastAPI router for Orchestrator endpoints."""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from langflow.services.database.service import get_session
from langflow.services.database.models.project.model import OrchestrationRun, Project
from langflow.custom.orchestrator.service import (
    OrchestratorService,
    OrchestrationPipeline,
    StepInput,
    ModelType,
)
from langflow.custom.orchestrator.schemas import (
    PipelineCreateSchema,
    PipelineExecutionSchema,
    ExecutionSummarySchema,
    StepInputSchema,
)

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


def get_orchestrator_service(session: Session = Depends(get_session)) -> OrchestratorService:
    """Dependency injection for OrchestratorService."""
    return OrchestratorService(session)


@router.post(
    "/projects/{project_id}/execute",
    response_model=PipelineExecutionSchema,
    status_code=202,
)
def execute_pipeline(
    project_id: UUID,
    pipeline: PipelineCreateSchema,
    service: OrchestratorService = Depends(get_orchestrator_service),
    session: Session = Depends(get_session),
) -> PipelineExecutionSchema:
    """
    Execute an orchestration pipeline.
    
    This endpoint:
    1. Creates an orchestration run
    2. Executes steps sequentially with different models
    3. Captures artifacts from each step
    4. Runs the Assembler model to combine and clean outputs
    5. Saves the final result to the database
    
    Returns:
        PipelineExecutionSchema with execution results and artifacts
    """
    # Verify project exists
    project = session.exec(
        select(Project).where(Project.id == project_id)
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create orchestration run
    run = OrchestrationRun(
        project_id=project_id,
        status="PENDING",
        steps={s.step_name: s.model_type for s in pipeline.steps},
    )
    session.add(run)
    session.commit()
    session.refresh(run)

    # Convert schema steps to service StepInput objects
    steps = [
        StepInput(
            step_name=s.step_name,
            model_type=ModelType(s.model_type),
            prompt=s.prompt,
            context=s.context or {},
            parameters=s.parameters or {},
        )
        for s in pipeline.steps
    ]

    # Build pipeline object
    orchestration_pipeline = OrchestrationPipeline(
        project_id=project_id,
        name=pipeline.name,
        steps=steps,
        global_context=pipeline.global_context or {},
        metadata=pipeline.metadata or {},
    )

    # Execute pipeline (this is an async operation, so we return 202 Accepted)
    try:
        result = service.execute_pipeline(orchestration_pipeline, run.id)
        
        return PipelineExecutionSchema(
            run_id=str(run.id),
            project_id=str(project_id),
            status=result.get("status", "UNKNOWN"),
            steps=result.get("steps", []),
            final_artifacts=result.get("final_artifacts", []),
            assembled_code=result.get("assembled_code"),
            started_at=result.get("started_at", ""),
            finished_at=result.get("finished_at", ""),
            error=result.get("error"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {str(e)}"
        )


@router.get(
    "/runs/{run_id}",
    response_model=ExecutionSummarySchema,
)
def get_run_summary(
    run_id: UUID,
    service: OrchestratorService = Depends(get_orchestrator_service),
    session: Session = Depends(get_session),
) -> ExecutionSummarySchema:
    """
    Get the execution summary of an orchestration run.
    
    Returns:
        ExecutionSummarySchema with step history and statistics
    """
    # Verify run exists in database
    run = session.exec(
        select(OrchestrationRun).where(OrchestrationRun.id == run_id)
    ).first()
    if not run:
        raise HTTPException(status_code=404, detail="Orchestration run not found")

    summary = service.get_run_summary(run_id)
    
    return ExecutionSummarySchema(
        run_id=summary.get("run_id", ""),
        total_steps=summary.get("total_steps", 0),
        successful_steps=summary.get("successful_steps", 0),
        failed_steps=summary.get("failed_steps", 0),
        total_execution_time=summary.get("total_execution_time", 0.0),
        steps=summary.get("steps", []),
    )


@router.get("/models")
def list_available_models():
    """
    List available models for orchestration.
    
    Returns:
        List of supported model types with descriptions
    """
    return {
        "models": [
            {
                "name": "CodeLlama",
                "description": "Meta's CodeLlama - Code generation and understanding",
                "capabilities": ["code_generation", "code_analysis", "refactoring"],
                "recommended_for": ["Initial analysis", "Code generation"],
            },
            {
                "name": "CodeGemma",
                "description": "Google's CodeGemma - Specialized code model",
                "capabilities": ["code_generation", "code_explanation", "bug_fixing"],
                "recommended_for": ["Code refinement", "Bug fixing"],
            },
            {
                "name": "T5Gemma",
                "description": "T5Gemma - Text-to-text transfer transformer",
                "capabilities": ["text_transformation", "summarization", "translation"],
                "recommended_for": ["Code transformation", "Documentation generation"],
            },
            {
                "name": "Assembler",
                "description": "Final assembly model - Combines and polishes outputs",
                "capabilities": ["code_assembly", "optimization", "validation"],
                "recommended_for": ["Final assembly (automatic)"],
            },
        ]
    }


@router.get("/templates")
def list_pipeline_templates():
    """
    List predefined pipeline templates.
    
    Returns:
        List of example pipelines for common tasks
    """
    return {
        "templates": [
            {
                "name": "React Component Pipeline",
                "description": "Generate production-ready React components",
                "steps": [
                    {
                        "step_name": "analyze_requirements",
                        "model_type": "CodeLlama",
                        "prompt": "Analyze the component requirements and create a design plan",
                    },
                    {
                        "step_name": "generate_component",
                        "model_type": "CodeGemma",
                        "prompt": "Generate a well-structured React component based on the design plan",
                    },
                    {
                        "step_name": "optimize_code",
                        "model_type": "T5Gemma",
                        "prompt": "Optimize and refactor the component code",
                    },
                ],
            },
            {
                "name": "Python Module Pipeline",
                "description": "Generate production-ready Python modules",
                "steps": [
                    {
                        "step_name": "design_architecture",
                        "model_type": "CodeLlama",
                        "prompt": "Design the module architecture and API",
                    },
                    {
                        "step_name": "implement_core",
                        "model_type": "CodeGemma",
                        "prompt": "Implement the core functionality",
                    },
                    {
                        "step_name": "add_testing",
                        "model_type": "T5Gemma",
                        "prompt": "Add comprehensive unit tests",
                    },
                ],
            },
            {
                "name": "UI Kit Pipeline",
                "description": "Generate a complete UI component library",
                "steps": [
                    {
                        "step_name": "design_system",
                        "model_type": "CodeLlama",
                        "prompt": "Define design system tokens and guidelines",
                    },
                    {
                        "step_name": "generate_components",
                        "model_type": "CodeGemma",
                        "prompt": "Generate base components from design system",
                    },
                    {
                        "step_name": "generate_stories",
                        "model_type": "T5Gemma",
                        "prompt": "Generate Storybook stories for components",
                    },
                ],
            },
        ]
    }
