"""
Model Runtime Manager - Extensible architecture for local + remote model execution.
Supports multiple backends: transformers, llama-cpp, ollama, etc.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import asyncio
from abc import ABC, abstractmethod
from uuid import uuid4


class RuntimeType(str, Enum):
    """Types of supported runtimes."""
    TRANSFORMERS = "transformers"        # HuggingFace transformers + PyTorch
    LLAMA_CPP = "llama_cpp"             # llama.cpp for quantized models
    OLLAMA = "ollama"                    # Ollama (local LLM server)
    VLLM = "vllm"                        # vLLM (high-throughput inference)
    CUDA = "cuda"                        # NVIDIA CUDA
    MPS = "mps"                          # Apple Metal Performance Shaders
    TPU = "tpu"                          # Google TPU


class DeviceType(str, Enum):
    """Device types for model execution."""
    CPU = "cpu"
    GPU = "gpu"
    MPS = "mps"                          # Apple Silicon
    TPU = "tpu"
    AUTO = "auto"                        # Auto-detect


@dataclass
class ModelConfig:
    """Configuration for a model."""
    model_id: str                        # Model identifier (HF model_id or path)
    model_name: str                      # Human-readable name
    model_type: str                      # Type: "llm", "coder", "embedding", "image"
    runtime_type: RuntimeType            # Runtime to use
    device_type: DeviceType = DeviceType.AUTO
    quantization: Optional[str] = None   # "int8", "int4", "fp16", etc.
    max_tokens: int = 512
    batch_size: int = 1
    cache_size: int = 1024               # MB for KV cache
    parameters: Dict[str, Any] = None   # Runtime-specific parameters
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class GenerationConfig:
    """Configuration for generation request."""
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 50
    repetition_penalty: float = 1.0
    stream: bool = False


@dataclass
class GenerationResult:
    """Result from generation."""
    text: str
    model_name: str
    tokens_generated: int
    execution_time: float
    metadata: Dict[str, Any] = None


# ============ ABSTRACT RUNTIME BASE CLASS ============

class ModelRuntime(ABC):
    """Abstract base class for model runtimes."""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.is_loaded = False

    @abstractmethod
    async def load(self) -> bool:
        """Load the model into memory."""
        pass

    @abstractmethod
    async def unload(self) -> None:
        """Unload the model from memory."""
        pass

    @abstractmethod
    async def generate(self, gen_config: GenerationConfig) -> GenerationResult:
        """Generate text based on prompt."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check runtime health."""
        pass

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage (MB)."""
        return {"total_mb": 0, "used_mb": 0}


# ============ TRANSFORMERS RUNTIME ============

class TransformersRuntime(ModelRuntime):
    """Runtime for HuggingFace transformers + PyTorch."""

    async def load(self) -> bool:
        """Load model using transformers."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch

            device = self._map_device()
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_id)
            
            torch_dtype = torch.float16 if self.config.quantization == "fp16" else torch.bfloat16
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_id,
                torch_dtype=torch_dtype,
                device_map=device,
                load_in_8bit=self.config.quantization == "int8",
                load_in_4bit=self.config.quantization == "int4",
            )
            
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"Error loading transformers model: {e}")
            return False

    async def unload(self) -> None:
        """Unload model."""
        if self.model:
            import torch
            del self.model
            del self.tokenizer
            torch.cuda.empty_cache()
            self.is_loaded = False

    async def generate(self, gen_config: GenerationConfig) -> GenerationResult:
        """Generate text."""
        import time
        import torch

        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        start_time = time.time()
        inputs = self.tokenizer(gen_config.prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=gen_config.max_tokens,
                temperature=gen_config.temperature,
                top_p=gen_config.top_p,
                top_k=gen_config.top_k,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        result_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
        elapsed = time.time() - start_time

        return GenerationResult(
            text=result_text,
            model_name=self.config.model_name,
            tokens_generated=len(output[0]) - len(inputs["input_ids"][0]),
            execution_time=elapsed,
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check health."""
        import torch
        return {
            "status": "healthy" if self.is_loaded else "not_loaded",
            "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
            "cuda_available": torch.cuda.is_available(),
        }

    def _map_device(self) -> str:
        """Map device type to torch device string."""
        import torch
        
        if self.config.device_type == DeviceType.AUTO:
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            return "cpu"
        elif self.config.device_type == DeviceType.MPS:
            return "mps" if torch.backends.mps.is_available() else "cpu"
        elif self.config.device_type == DeviceType.GPU:
            return "cuda" if torch.cuda.is_available() else "cpu"
        return "cpu"


# ============ LLAMA.CPP RUNTIME ============

class LlamaCppRuntime(ModelRuntime):
    """Runtime for llama.cpp (quantized GGUF models)."""

    async def load(self) -> bool:
        """Load model using llama-cpp-python."""
        try:
            from llama_cpp import Llama

            n_gpu_layers = -1 if self.config.device_type in (DeviceType.GPU, DeviceType.AUTO) else 0
            
            self.model = Llama(
                model_path=self.config.model_id,
                n_gpu_layers=n_gpu_layers,
                n_threads=8,
                verbose=False,
            )
            
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"Error loading llama.cpp model: {e}")
            return False

    async def unload(self) -> None:
        """Unload model."""
        if self.model:
            del self.model
            self.is_loaded = False

    async def generate(self, gen_config: GenerationConfig) -> GenerationResult:
        """Generate text."""
        import time

        if not self.is_loaded:
            raise RuntimeError("Model not loaded")

        start_time = time.time()
        
        output = self.model(
            gen_config.prompt,
            max_tokens=gen_config.max_tokens,
            temperature=gen_config.temperature,
            top_p=gen_config.top_p,
            top_k=gen_config.top_k,
            repeat_penalty=gen_config.repetition_penalty,
        )

        result_text = output["choices"][0]["text"]
        elapsed = time.time() - start_time

        return GenerationResult(
            text=result_text,
            model_name=self.config.model_name,
            tokens_generated=output.get("usage", {}).get("completion_tokens", 0),
            execution_time=elapsed,
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check health."""
        return {
            "status": "healthy" if self.is_loaded else "not_loaded",
            "model_path": self.config.model_id,
        }


# ============ RUNTIME MANAGER ============

class RuntimeManager:
    """
    Central manager for model runtimes.
    
    Features:
    - Load/unload models on demand
    - Route requests to appropriate runtime
    - Cache loaded models
    - Support for multiple model types
    - Extensible for new runtimes
    """

    def __init__(self):
        self.runtimes: Dict[str, ModelRuntime] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.loaded_models: Dict[str, ModelRuntime] = {}

    def register_model(self, config: ModelConfig) -> bool:
        """Register a model configuration."""
        try:
            runtime = self._create_runtime(config)
            self.model_configs[config.model_name] = config
            self.runtimes[config.model_name] = runtime
            return True
        except Exception as e:
            print(f"Error registering model {config.model_name}: {e}")
            return False

    def _create_runtime(self, config: ModelConfig) -> ModelRuntime:
        """Factory method to create appropriate runtime."""
        if config.runtime_type == RuntimeType.TRANSFORMERS:
            return TransformersRuntime(config)
        elif config.runtime_type == RuntimeType.LLAMA_CPP:
            return LlamaCppRuntime(config)
        else:
            raise ValueError(f"Unsupported runtime type: {config.runtime_type}")

    async def load_model(self, model_name: str) -> bool:
        """Load a model into memory."""
        if model_name in self.loaded_models:
            return True

        if model_name not in self.runtimes:
            raise ValueError(f"Model {model_name} not registered")

        runtime = self.runtimes[model_name]
        success = await runtime.load()
        
        if success:
            self.loaded_models[model_name] = runtime
        
        return success

    async def unload_model(self, model_name: str) -> None:
        """Unload a model from memory."""
        if model_name in self.loaded_models:
            runtime = self.loaded_models[model_name]
            await runtime.unload()
            del self.loaded_models[model_name]

    async def generate(
        self,
        model_name: str,
        gen_config: GenerationConfig,
    ) -> GenerationResult:
        """Generate text using specified model."""
        if model_name not in self.loaded_models:
            await self.load_model(model_name)

        runtime = self.loaded_models[model_name]
        return await runtime.generate(gen_config)

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all loaded models."""
        health = {
            "registered_models": len(self.model_configs),
            "loaded_models": len(self.loaded_models),
            "models": {},
        }

        for model_name, runtime in self.loaded_models.items():
            health["models"][model_name] = await runtime.health_check()

        return health

    def list_models(self) -> List[Dict[str, Any]]:
        """List all registered models."""
        models = []
        for name, config in self.model_configs.items():
            models.append({
                "name": name,
                "model_id": config.model_id,
                "type": config.model_type,
                "runtime": config.runtime_type.value,
                "loaded": name in self.loaded_models,
            })
        return models

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a model."""
        if model_name not in self.model_configs:
            return None

        config = self.model_configs[model_name]
        return {
            "name": config.model_name,
            "model_id": config.model_id,
            "type": config.model_type,
            "runtime": config.runtime_type.value,
            "device": config.device_type.value,
            "quantization": config.quantization,
            "max_tokens": config.max_tokens,
            "loaded": model_name in self.loaded_models,
            "cache_size_mb": config.cache_size,
        }


# ============ PREDEFINED MODEL CONFIGS ============

def get_default_models() -> List[ModelConfig]:
    """Get default model configurations for common use cases."""
    return [
        # Gemma 2B - Lightweight, fast
        ModelConfig(
            model_id="google/gemma-2b",
            model_name="Gemma-2B",
            model_type="llm",
            runtime_type=RuntimeType.TRANSFORMERS,
            device_type=DeviceType.AUTO,
            quantization="int8",
            max_tokens=512,
        ),
        # Gemma 7B - Balance between speed and quality
        ModelConfig(
            model_id="google/gemma-7b",
            model_name="Gemma-7B",
            model_type="llm",
            runtime_type=RuntimeType.TRANSFORMERS,
            device_type=DeviceType.AUTO,
            quantization="fp16",
            max_tokens=1024,
        ),
        # CodeLlama 7B - Code generation (GGUF quantized)
        ModelConfig(
            model_id="./models/codellama-7b.gguf",
            model_name="CodeLlama-7B-GGUF",
            model_type="coder",
            runtime_type=RuntimeType.LLAMA_CPP,
            device_type=DeviceType.AUTO,
            quantization="Q4_K_M",
            max_tokens=1024,
        ),
        # Mistral 7B - Fast, capable
        ModelConfig(
            model_id="mistralai/Mistral-7B-Instruct-v0.1",
            model_name="Mistral-7B",
            model_type="llm",
            runtime_type=RuntimeType.TRANSFORMERS,
            device_type=DeviceType.AUTO,
            quantization="int8",
            max_tokens=2048,
        ),
    ]
