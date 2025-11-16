"""
FastAPI routes for local model runtime management.
Endpoints for loading, unloading, and generating with local models.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Import runtime manager
try:
    from langflow.custom.runtimes.manager import (
        RuntimeManager,
        ModelConfig,
        GenerationConfig,
        RuntimeType,
        DeviceType,
        get_default_models,
    )
except ImportError:
    RuntimeManager = None
    ModelConfig = None
    GenerationConfig = None


# ============ PYDANTIC MODELS ============

class ModelRegistrationRequest(BaseModel):
    """Request to register a new model."""
    model_id: str
    model_name: str
    model_type: str  # "llm", "coder", "embedding", "image"
    runtime_type: str  # "transformers", "llama_cpp", "ollama"
    device_type: Optional[str] = "auto"
    quantization: Optional[str] = None
    max_tokens: Optional[int] = 512
    cache_size: Optional[int] = 1024


class GenerationRequest(BaseModel):
    """Request to generate text."""
    model_name: str
    prompt: str
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.95
    top_k: Optional[int] = 50
    repetition_penalty: Optional[float] = 1.0


class GenerationResponse(BaseModel):
    """Response from generation."""
    text: str
    model_name: str
    tokens_generated: int
    execution_time: float
    metadata: Optional[dict] = None


class ModelInfo(BaseModel):
    """Information about a registered model."""
    name: str
    model_id: str
    type: str
    runtime: str
    device: str
    quantization: Optional[str]
    max_tokens: int
    loaded: bool
    cache_size_mb: int


class RuntimeHealth(BaseModel):
    """Health status of runtime."""
    status: str
    registered_models: int
    loaded_models: int
    models: dict


# ============ GLOBAL RUNTIME MANAGER ============

_runtime_manager: Optional[RuntimeManager] = None


def get_runtime_manager() -> RuntimeManager:
    """Get or create the global runtime manager."""
    global _runtime_manager
    if _runtime_manager is None:
        _runtime_manager = RuntimeManager()
        # Register default models
        for config in get_default_models():
            _runtime_manager.register_model(config)
    return _runtime_manager


# ============ ROUTER ============

router = APIRouter(prefix="/api/v1/runtime", tags=["Runtime Manager"])


@router.post("/models/register", response_model=dict)
async def register_model(request: ModelRegistrationRequest):
    """
    Register a new model with the runtime manager.
    
    **Parameters:**
    - model_id: HuggingFace model ID or local path to GGUF
    - model_name: Human-readable name
    - model_type: "llm", "coder", "embedding", etc.
    - runtime_type: "transformers", "llama_cpp", "ollama"
    - device_type: "cpu", "gpu", "mps", "auto"
    - quantization: "int8", "int4", "fp16", or None
    """
    try:
        manager = get_runtime_manager()
        
        config = ModelConfig(
            model_id=request.model_id,
            model_name=request.model_name,
            model_type=request.model_type,
            runtime_type=RuntimeType(request.runtime_type),
            device_type=DeviceType(request.device_type or "auto"),
            quantization=request.quantization,
            max_tokens=request.max_tokens or 512,
            cache_size=request.cache_size or 1024,
        )
        
        success = manager.register_model(config)
        
        if success:
            return {
                "status": "registered",
                "model_name": request.model_name,
                "model_id": request.model_id,
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to register model")
            
    except Exception as e:
        logger.error(f"Error registering model: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/models/load")
async def load_model(model_name: str = Query(..., description="Name of model to load")):
    """
    Load a registered model into memory.
    This may take a few minutes depending on model size.
    """
    try:
        manager = get_runtime_manager()
        success = await manager.load_model(model_name)
        
        if success:
            return {
                "status": "loaded",
                "model_name": model_name,
                "message": f"Model {model_name} loaded successfully",
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to load model {model_name}")
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error loading model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/unload")
async def unload_model(model_name: str = Query(..., description="Name of model to unload")):
    """Unload a model from memory to free resources."""
    try:
        manager = get_runtime_manager()
        await manager.unload_model(model_name)
        
        return {
            "status": "unloaded",
            "model_name": model_name,
            "message": f"Model {model_name} unloaded successfully",
        }
            
    except Exception as e:
        logger.error(f"Error unloading model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=GenerationResponse)
async def generate_text(request: GenerationRequest):
    """
    Generate text using a local model.
    
    **Parameters:**
    - model_name: Name of the model to use
    - prompt: The input prompt
    - max_tokens: Maximum tokens to generate
    - temperature: Sampling temperature (0.0-2.0)
    - top_p: Nucleus sampling parameter (0.0-1.0)
    - top_k: Top-k sampling parameter
    - repetition_penalty: Penalty for repeated tokens
    
    **Response:**
    - text: Generated text
    - tokens_generated: Number of tokens generated
    - execution_time: Time taken in seconds
    """
    try:
        manager = get_runtime_manager()
        
        gen_config = GenerationConfig(
            prompt=request.prompt,
            max_tokens=request.max_tokens or 512,
            temperature=request.temperature or 0.7,
            top_p=request.top_p or 0.95,
            top_k=request.top_k or 50,
            repetition_penalty=request.repetition_penalty or 1.0,
        )
        
        result = await manager.generate(request.model_name, gen_config)
        
        return GenerationResponse(
            text=result.text,
            model_name=result.model_name,
            tokens_generated=result.tokens_generated,
            execution_time=result.execution_time,
            metadata=result.metadata,
        )
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=List[dict])
async def list_models():
    """
    List all registered models.
    
    **Response:**
    List of models with:
    - name: Model name
    - model_id: HuggingFace model ID
    - type: Model type (llm, coder, etc.)
    - runtime: Runtime type (transformers, llama_cpp)
    - loaded: Whether model is currently loaded
    """
    try:
        manager = get_runtime_manager()
        return manager.list_models()
    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_name}", response_model=Optional[ModelInfo])
async def get_model_info(model_name: str):
    """Get detailed information about a specific model."""
    try:
        manager = get_runtime_manager()
        info = manager.get_model_info(model_name)
        
        if info is None:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        return ModelInfo(**info)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=RuntimeHealth)
async def health_check():
    """
    Check health of the runtime manager.
    
    **Response:**
    - status: Overall status
    - registered_models: Number of registered models
    - loaded_models: Number of currently loaded models
    - models: Health info for each loaded model
    """
    try:
        manager = get_runtime_manager()
        health = await manager.health_check()
        return RuntimeHealth(**health)
            
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/stats")
async def get_stats():
    """Get detailed statistics about runtime usage."""
    try:
        manager = get_runtime_manager()
        
        stats = {
            "total_registered": len(manager.model_configs),
            "total_loaded": len(manager.loaded_models),
            "registered_models": list(manager.model_configs.keys()),
            "loaded_models": list(manager.loaded_models.keys()),
        }
        
        # Add memory info per model
        models_info = []
        for name, runtime in manager.loaded_models.items():
            memory = runtime.get_memory_usage()
            models_info.append({
                "name": name,
                "memory_used_mb": memory["used_mb"],
                "memory_total_mb": memory["total_mb"],
            })
        
        stats["models_memory"] = models_info
        return stats
            
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unload-all")
async def unload_all(background_tasks: BackgroundTasks):
    """
    Unload all loaded models from memory.
    This is useful for freeing resources when done.
    """
    try:
        manager = get_runtime_manager()
        models_to_unload = list(manager.loaded_models.keys())
        
        # Unload in background
        async def unload_all_models():
            for model_name in models_to_unload:
                try:
                    await manager.unload_model(model_name)
                except Exception as e:
                    logger.error(f"Error unloading {model_name}: {e}")
        
        background_tasks.add_task(unload_all_models)
        
        return {
            "status": "unloading",
            "models_count": len(models_to_unload),
            "message": "All models will be unloaded in the background",
        }
            
    except Exception as e:
        logger.error(f"Error unloading all models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
