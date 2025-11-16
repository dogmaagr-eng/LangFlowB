"""FastAPI routes for Framer component generation."""

from uuid import UUID
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session

try:
    from langflow.services.database.service import get_session
except (ImportError, AttributeError):
    try:
        from langflow.services.database import get_session
    except ImportError:
        def get_session():
            """Fallback get_session function"""
            pass
from .service import (
    FramerComponentGenerator,
    FramerExportResult,
    ComponentType,
    AnimationType,
)

router = APIRouter(
    prefix="/api/v1/framer",
    tags=["framer"],
    responses={404: {"description": "Not found"}},
)


# ============ COMPONENT CONVERSION ============

@router.post(
    "/convert",
    response_model=Dict[str, Any],
    summary="Convert orchestrator artifacts to Framer components",
    description="Transform JSX/TSX artifacts from orchestrator to Framer-compatible components",
)
async def convert_to_framer(
    run_id: UUID,
    artifacts: List[Dict[str, Any]],
    project_metadata: Optional[Dict[str, Any]] = None,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Convert orchestrator artifacts to Framer components.
    
    Request body example:
    ```json
    {
        "run_id": "uuid",
        "artifacts": [
            {
                "type": "jsx",
                "name": "Button.jsx",
                "content": "export const Button = () => ..."
            }
        ],
        "project_metadata": {
            "canvas_width": 1200,
            "canvas_height": 800
        }
    }
    ```
    
    Returns:
    - List of FramerExportResult objects
    - Canvas configurations
    - Animation definitions
    """
    try:
        generator = FramerComponentGenerator(session)
        results = generator.convert_artifacts_to_framer(
            run_id=run_id,
            artifacts=artifacts,
            project_metadata=project_metadata,
        )

        # Save to database
        for result in results:
            if result.status == "SUCCESS":
                generator.save_framer_component(
                    run_id=run_id,
                    project_id=UUID("00000000-0000-0000-0000-000000000000"),  # Would come from context
                    result=result,
                )

        return {
            "status": "SUCCESS",
            "run_id": str(run_id),
            "components_generated": len(results),
            "results": [
                {
                    "component_id": r.component_id,
                    "component_name": r.component_name,
                    "status": r.status,
                    "generation_time": r.generation_time,
                    "error": r.error,
                    "artifacts_count": len(r.artifacts),
                }
                for r in results
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Framer conversion failed: {str(e)}",
        )


@router.post(
    "/components/{run_id}",
    response_model=Dict[str, Any],
    summary="Get generated Framer components",
    description="Retrieve Framer components generated for a specific orchestration run",
)
async def get_framer_components(
    run_id: UUID,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Get all Framer components generated for a run.
    
    Args:
        run_id: UUID of the orchestration run
        
    Returns:
        List of Framer components with metadata
    """
    try:
        from langflow.services.database.models.project.model import GeneratedArtifact

        artifacts = session.query(GeneratedArtifact).filter(
            GeneratedArtifact.run_id == run_id
        ).filter(
            GeneratedArtifact.artifact_type == "framer_component"
        ).all()

        if not artifacts:
            return {
                "status": "NO_COMPONENTS",
                "run_id": str(run_id),
                "components": [],
            }

        return {
            "status": "SUCCESS",
            "run_id": str(run_id),
            "components": [
                {
                    "id": str(a.id),
                    "name": a.name,
                    "type": a.artifact_type,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "metadata": a.metadata,
                }
                for a in artifacts
            ],
            "count": len(artifacts),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve components: {str(e)}",
        )


@router.get(
    "/component/{artifact_id}",
    response_model=Dict[str, Any],
    summary="Get Framer component code",
    description="Retrieve the full Framer component code and metadata",
)
async def get_component_code(
    artifact_id: UUID,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Get full Framer component code.
    
    Args:
        artifact_id: UUID of the artifact
        
    Returns:
        Complete component code and configuration
    """
    try:
        from langflow.services.database.models.project.model import GeneratedArtifact

        artifact = session.query(GeneratedArtifact).filter(
            GeneratedArtifact.id == artifact_id,
        ).first()

        if not artifact:
            raise HTTPException(
                status_code=404,
                detail="Component not found",
            )

        return {
            "status": "SUCCESS",
            "component": {
                "id": str(artifact.id),
                "name": artifact.name,
                "type": artifact.artifact_type,
                "code": artifact.content,
                "metadata": artifact.metadata,
                "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve component: {str(e)}",
        )


# ============ COMPONENT TYPES & ANIMATIONS ============

@router.get(
    "/component-types",
    response_model=Dict[str, Any],
    summary="List available component types",
    description="Get all supported Framer component types",
)
async def get_component_types() -> Dict[str, Any]:
    """Get list of supported component types."""
    return {
        "component_types": [ct.value for ct in ComponentType],
        "description": "Available component types for Framer canvas",
    }


@router.get(
    "/animation-types",
    response_model=Dict[str, Any],
    summary="List available animation types",
    description="Get all supported animation types for components",
)
async def get_animation_types() -> Dict[str, Any]:
    """Get list of supported animation types."""
    return {
        "animation_types": [at.value for at in AnimationType],
        "description": "Available animation types for interactive components",
    }


# ============ EXPORT & DOWNLOAD ============

@router.post(
    "/export/{artifact_id}",
    response_model=Dict[str, Any],
    summary="Export Framer component",
    description="Export component in various formats (TSX, JSON, HTML)",
)
async def export_component(
    artifact_id: UUID,
    export_format: str = "tsx",
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Export component in specified format.
    
    Args:
        artifact_id: UUID of the artifact
        export_format: Format to export ("tsx", "json", "html")
        
    Returns:
        Exported component data
    """
    try:
        from langflow.services.database.models.project.model import GeneratedArtifact

        artifact = session.query(GeneratedArtifact).filter(
            GeneratedArtifact.id == artifact_id,
        ).first()

        if not artifact:
            raise HTTPException(status_code=404, detail="Component not found")

        if export_format == "json":
            return {
                "format": "json",
                "component": {
                    "name": artifact.name,
                    "content": artifact.content,
                    "metadata": artifact.metadata,
                },
            }

        elif export_format == "html":
            # Generate HTML preview
            html_preview = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{artifact.name}</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
</head>
<body>
    <div id="root"></div>
    <script>
        // Component will be rendered here
        // Code preview for {artifact.name}
    </script>
</body>
</html>
"""
            return {
                "format": "html",
                "preview": html_preview,
                "component_name": artifact.name,
            }

        else:  # Default to TSX
            return {
                "format": "tsx",
                "component": artifact.content,
                "metadata": artifact.metadata,
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}",
        )


# ============ CANVAS OPERATIONS ============

@router.post(
    "/canvas/preview/{artifact_id}",
    response_model=Dict[str, Any],
    summary="Generate canvas preview",
    description="Generate interactive preview configuration for Framer canvas",
)
async def generate_canvas_preview(
    artifact_id: UUID,
    canvas_config: Optional[Dict[str, Any]] = None,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Generate canvas preview configuration.
    
    Args:
        artifact_id: UUID of the artifact
        canvas_config: Optional canvas configuration overrides
        
    Returns:
        Canvas preview configuration
    """
    try:
        from langflow.services.database.models.project.model import GeneratedArtifact

        artifact = session.query(GeneratedArtifact).filter(
            GeneratedArtifact.id == artifact_id,
        ).first()

        if not artifact:
            raise HTTPException(status_code=404, detail="Component not found")

        metadata = artifact.metadata or {}
        canvas = metadata.get("canvas_config", {})

        if canvas_config:
            canvas.update(canvas_config)

        return {
            "status": "SUCCESS",
            "artifact_id": str(artifact_id),
            "component_name": artifact.name,
            "canvas": canvas,
            "animations": metadata.get("animations_config", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Canvas preview generation failed: {str(e)}",
        )


# ============ BATCH OPERATIONS ============

@router.post(
    "/batch/convert",
    response_model=Dict[str, Any],
    summary="Batch convert multiple components",
    description="Convert multiple orchestrator artifacts in a single request",
)
async def batch_convert(
    batch_data: Dict[str, Any],
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Batch convert multiple components.
    
    Request body:
    ```json
    {
        "runs": [
            {"run_id": "uuid", "artifacts": [...]},
            ...
        ],
        "project_metadata": {...}
    }
    ```
    """
    try:
        generator = FramerComponentGenerator(session)
        runs = batch_data.get("runs", [])
        project_metadata = batch_data.get("project_metadata", {})

        all_results = []
        for run_data in runs:
            run_id = UUID(run_data.get("run_id"))
            artifacts = run_data.get("artifacts", [])

            results = generator.convert_artifacts_to_framer(
                run_id=run_id,
                artifacts=artifacts,
                project_metadata=project_metadata,
            )
            all_results.extend(results)

        return {
            "status": "SUCCESS",
            "batch_size": len(runs),
            "components_generated": len(all_results),
            "summary": {
                "successful": sum(1 for r in all_results if r.status == "SUCCESS"),
                "failed": sum(1 for r in all_results if r.status == "FAILED"),
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch conversion failed: {str(e)}",
        )


# ============ HEALTH & STATUS ============

@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Framer service health check",
    description="Check if Framer component generator service is operational",
)
async def health_check() -> Dict[str, Any]:
    """Health check for Framer service."""
    return {
        "status": "HEALTHY",
        "service": "Framer Component Generator",
        "version": "1.0.0",
        "features": [
            "JSX/TSX to Framer conversion",
            "Interactive component generation",
            "Canvas configuration",
            "Animation support",
            "Multi-format export",
        ],
    }


@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="Framer service statistics",
    description="Get statistics about generated components",
)
async def get_statistics(
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Get Framer service statistics."""
    try:
        from langflow.services.database.models.project.model import GeneratedArtifact

        total_components = session.query(GeneratedArtifact).filter(
            GeneratedArtifact.artifact_type == "framer_component",
        ).count()

        return {
            "status": "SUCCESS",
            "statistics": {
                "total_components": total_components,
                "service": "Framer Component Generator",
                "version": "1.0.0",
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Statistics retrieval failed: {str(e)}",
        )
