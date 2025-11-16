"""FastAPI routes for Gemini 2.5 Pro integration."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session

from langflow.services.database.service import get_session
from .service import (
    GeminiIntegration,
    EnhancementType,
    EnhancementResult,
    GEMINI_AVAILABLE,
)

router = APIRouter(
    prefix="/api/v1/gemini",
    tags=["gemini"],
    responses={404: {"description": "Not found"}},
)


# ============ ENHANCEMENT OPERATIONS ============

@router.post(
    "/enhance/prompt",
    response_model=Dict[str, Any],
    summary="Clean and optimize prompt",
    description="Use Gemini 2.5 Pro to clean and optimize a prompt for better results",
)
async def clean_prompt(
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Clean and optimize a prompt using Gemini.
    
    Args:
        prompt: Original prompt text
        context: Optional context about the prompt
        
    Returns:
        Enhanced prompt and quality metrics
    """
    if not GEMINI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Gemini service not available. Check GOOGLE_API_KEY environment variable.",
        )

    try:
        integration = GeminiIntegration()
        result = integration.clean_prompt(prompt, context)

        if result.status == "FAILED":
            raise HTTPException(
                status_code=500,
                detail=f"Prompt cleaning failed: {result.error}",
            )

        return {
            "status": "SUCCESS",
            "enhancement_type": result.enhancement_type.value,
            "original": result.original_content,
            "enhanced": result.enhanced_content,
            "quality_improvement": result.quality_score_after - result.quality_score_before,
            "generation_time": result.generation_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prompt cleaning failed: {str(e)}",
        )


@router.post(
    "/enhance/code/quality",
    response_model=Dict[str, Any],
    summary="Enhance code quality",
    description="Use Gemini 2.5 Pro to improve code quality and best practices",
)
async def enhance_code_quality(
    code: str,
    language: str = Query("javascript", description="Programming language (javascript, typescript, python, etc)"),
) -> Dict[str, Any]:
    """
    Enhance code quality using Gemini.
    
    Args:
        code: Source code to enhance
        language: Programming language
        
    Returns:
        Enhanced code and quality metrics
    """
    if not GEMINI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Gemini service not available",
        )

    try:
        integration = GeminiIntegration()
        result = integration.enhance_code_quality(code, language)

        if result.status == "FAILED":
            raise HTTPException(
                status_code=500,
                detail=f"Code enhancement failed: {result.error}",
            )

        return {
            "status": "SUCCESS",
            "enhancement_type": result.enhancement_type.value,
            "language": language,
            "original_length": len(code),
            "enhanced_length": len(result.enhanced_content),
            "quality_improvement": result.quality_score_after - result.quality_score_before,
            "code": result.enhanced_content,
            "generation_time": result.generation_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Code enhancement failed: {str(e)}",
        )


@router.post(
    "/enhance/accessibility",
    response_model=Dict[str, Any],
    summary="Enhance component accessibility",
    description="Improve JSX/TSX component for WCAG compliance and accessibility",
)
async def enhance_accessibility(
    jsx_code: str,
) -> Dict[str, Any]:
    """
    Enhance component accessibility.
    
    Args:
        jsx_code: React component code
        
    Returns:
        Enhanced component with accessibility improvements
    """
    if not GEMINI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Gemini service not available",
        )

    try:
        integration = GeminiIntegration()
        result = integration.enhance_accessibility(jsx_code)

        if result.status == "FAILED":
            raise HTTPException(
                status_code=500,
                detail=f"Accessibility enhancement failed: {result.error}",
            )

        return {
            "status": "SUCCESS",
            "enhancement_type": result.enhancement_type.value,
            "code": result.enhanced_content,
            "suggestions": result.suggestions,
            "generation_time": result.generation_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Accessibility enhancement failed: {str(e)}",
        )


@router.post(
    "/enhance/performance",
    response_model=Dict[str, Any],
    summary="Optimize code performance",
    description="Use Gemini 2.5 Pro to optimize code for better performance",
)
async def enhance_performance(
    code: str,
    language: str = Query("javascript", description="Programming language"),
) -> Dict[str, Any]:
    """
    Enhance code performance.
    
    Args:
        code: Source code
        language: Programming language
        
    Returns:
        Performance optimized code
    """
    if not GEMINI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Gemini service not available",
        )

    try:
        integration = GeminiIntegration()
        result = integration.enhance_performance(code, language)

        if result.status == "FAILED":
            raise HTTPException(
                status_code=500,
                detail=f"Performance enhancement failed: {result.error}",
            )

        return {
            "status": "SUCCESS",
            "enhancement_type": result.enhancement_type.value,
            "code": result.enhanced_content,
            "suggestions": result.suggestions,
            "generation_time": result.generation_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Performance enhancement failed: {str(e)}",
        )


@router.post(
    "/enhance/security",
    response_model=Dict[str, Any],
    summary="Enhance code security",
    description="Identify and fix security vulnerabilities in code",
)
async def enhance_security(
    code: str,
    language: str = Query("javascript", description="Programming language"),
) -> Dict[str, Any]:
    """
    Enhance code security.
    
    Args:
        code: Source code
        language: Programming language
        
    Returns:
        Secure code with fixes
    """
    if not GEMINI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Gemini service not available",
        )

    try:
        integration = GeminiIntegration()
        result = integration.enhance_security(code, language)

        if result.status == "FAILED":
            raise HTTPException(
                status_code=500,
                detail=f"Security enhancement failed: {result.error}",
            )

        return {
            "status": "SUCCESS",
            "enhancement_type": result.enhancement_type.value,
            "code": result.enhanced_content,
            "suggestions": result.suggestions,
            "generation_time": result.generation_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Security enhancement failed: {str(e)}",
        )


@router.post(
    "/enhance/documentation",
    response_model=Dict[str, Any],
    summary="Add documentation to code",
    description="Add comprehensive JSDoc/docstring documentation",
)
async def add_documentation(
    code: str,
    language: str = Query("javascript", description="Programming language"),
) -> Dict[str, Any]:
    """
    Add documentation to code.
    
    Args:
        code: Source code
        language: Programming language
        
    Returns:
        Code with added documentation
    """
    if not GEMINI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Gemini service not available",
        )

    try:
        integration = GeminiIntegration()
        result = integration.add_documentation(code, language)

        if result.status == "FAILED":
            raise HTTPException(
                status_code=500,
                detail=f"Documentation enhancement failed: {result.error}",
            )

        return {
            "status": "SUCCESS",
            "enhancement_type": result.enhancement_type.value,
            "code": result.enhanced_content,
            "generation_time": result.generation_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Documentation enhancement failed: {str(e)}",
        )


# ============ BATCH OPERATIONS ============

@router.post(
    "/enhance/batch",
    response_model=Dict[str, Any],
    summary="Batch enhancement",
    description="Apply enhancement to multiple items in one request",
)
async def batch_enhance(
    batch_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Apply enhancement to multiple items.
    
    Request body:
    ```json
    {
        "items": [
            {"content": "prompt text", "context": {...}},
            {"content": "code text", "language": "python"}
        ],
        "enhancement_type": "prompt_clean"
    }
    ```
    """
    if not GEMINI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Gemini service not available",
        )

    try:
        items = batch_data.get("items", [])
        enhancement_type_str = batch_data.get("enhancement_type", "prompt_clean")

        try:
            enhancement_type = EnhancementType(enhancement_type_str)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid enhancement type: {enhancement_type_str}",
            )

        integration = GeminiIntegration()
        results = integration.batch_enhance(items, enhancement_type)

        return {
            "status": "SUCCESS",
            "batch_size": len(items),
            "enhancement_type": enhancement_type_str,
            "results": [
                {
                    "status": r.status,
                    "content": r.enhanced_content if r.status == "SUCCESS" else None,
                    "error": r.error,
                    "generation_time": r.generation_time,
                }
                for r in results
            ],
            "successful": sum(1 for r in results if r.status == "SUCCESS"),
            "failed": sum(1 for r in results if r.status == "FAILED"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch enhancement failed: {str(e)}",
        )


# ============ ENHANCEMENT TYPES & CONFIG ============

@router.get(
    "/enhancement-types",
    response_model=Dict[str, Any],
    summary="List available enhancement types",
    description="Get all supported enhancement types",
)
async def get_enhancement_types() -> Dict[str, Any]:
    """Get list of supported enhancement types."""
    return {
        "enhancement_types": [et.value for et in EnhancementType],
        "descriptions": {
            "prompt_clean": "Clean and optimize prompts for better results",
            "code_quality": "Improve code quality and best practices",
            "accessibility": "Enhance WCAG compliance and accessibility",
            "performance": "Optimize code performance",
            "security": "Identify and fix security vulnerabilities",
            "documentation": "Add comprehensive documentation",
        },
    }


# ============ CONFIGURATION & STATUS ============

@router.get(
    "/config",
    response_model=Dict[str, Any],
    summary="Get Gemini configuration",
    description="Check Gemini service configuration status",
)
async def get_config() -> Dict[str, Any]:
    """Get Gemini configuration status."""
    is_configured, message = GeminiIntegration.check_api_key()

    return {
        "status": "CONFIGURED" if is_configured else "NOT_CONFIGURED",
        "available": GEMINI_AVAILABLE,
        "message": message,
        "model": "gemini-2.5-pro",
    }


@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Gemini service health check",
    description="Check if Gemini service is operational",
)
async def health_check() -> Dict[str, Any]:
    """Health check for Gemini service."""
    is_available = GeminiIntegration.is_available()
    is_configured, config_msg = GeminiIntegration.check_api_key()

    return {
        "status": "HEALTHY" if is_available else "UNAVAILABLE",
        "service": "Gemini 2.5 Pro Integration",
        "available": is_available,
        "configured": is_configured,
        "message": config_msg if not is_available else "Ready to serve requests",
        "version": "2.5-pro",
    }


@router.get(
    "/models",
    response_model=Dict[str, Any],
    summary="List available Gemini models",
    description="Get list of available Gemini models",
)
async def get_models() -> Dict[str, Any]:
    """List available Gemini models."""
    return {
        "models": [
            {
                "id": "gemini-2.5-pro",
                "name": "Gemini 2.5 Pro",
                "description": "Latest Gemini model (DOOOOS PUNTO CINCO PRO)",
                "status": "active",
            },
            {
                "id": "gemini-2.0-flash",
                "name": "Gemini 2.0 Flash",
                "description": "Fast inference model",
                "status": "available",
            },
            {
                "id": "gemini-1.5-pro",
                "name": "Gemini 1.5 Pro",
                "description": "Previous generation model",
                "status": "available",
            },
        ],
        "default": "gemini-2.5-pro",
    }


# ============ ERROR HANDLING ============

@router.get(
    "/info",
    response_model=Dict[str, Any],
    summary="Gemini integration information",
    description="Get information about Gemini integration",
)
async def get_info() -> Dict[str, Any]:
    """Get Gemini integration information."""
    is_available = GeminiIntegration.is_available()
    is_configured, config_msg = GeminiIntegration.check_api_key()

    return {
        "service": "Gemini 2.5 Pro Enhancement Layer",
        "version": "1.0.0",
        "available": is_available,
        "configured": is_configured,
        "capabilities": [
            "Prompt optimization",
            "Code quality enhancement",
            "Accessibility improvements",
            "Performance optimization",
            "Security vulnerability detection",
            "Documentation generation",
            "Batch operations",
        ],
        "models": ["gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-pro"],
        "setup_required": not is_configured,
        "setup_instructions": "Set GOOGLE_API_KEY environment variable with your Gemini API key" if not is_configured else None,
    }
