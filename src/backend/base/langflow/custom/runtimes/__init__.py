"""
Local Model Runtime Package
===========================

Extensible runtime manager for local model execution with support for:
- HuggingFace Transformers (PyTorch + MPS for Apple Silicon)
- llama.cpp (quantized GGUF models)
- Ollama (local LLM server)
- vLLM (high-throughput inference)

Includes specialized optimizations for:
- Google Gemma (2B, 7B, etc.)
- Code models (CodeLlama, CodeGemma)
- Embedding models

Architecture:
- RuntimeManager: Central orchestrator
- ModelRuntime: Abstract base class
- Specific runtimes: TransformersRuntime, LlamaCppRuntime, etc.
- ModelRegistry: Dynamic model registration for unlimited agent types
"""

from .manager import (
    RuntimeManager,
    ModelRuntime,
    ModelConfig,
    GenerationConfig,
    GenerationResult,
    RuntimeType,
    DeviceType,
    TransformersRuntime,
    LlamaCppRuntime,
    get_default_models,
)

from .gemma import (
    GemmaLocalRuntime,
    GemmaStreamingRuntime,
)

__all__ = [
    "RuntimeManager",
    "ModelRuntime",
    "ModelConfig",
    "GenerationConfig",
    "GenerationResult",
    "RuntimeType",
    "DeviceType",
    "TransformersRuntime",
    "LlamaCppRuntime",
    "GemmaLocalRuntime",
    "GemmaStreamingRuntime",
    "get_default_models",
]
