"""
Tests for Local Model Runtimes - Simplified version without full Langflow imports
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List
import time


# ============ INLINE DEFINITIONS (to avoid lfx import issues) ============

class RuntimeType(str, Enum):
    TRANSFORMERS = "transformers"
    LLAMA_CPP = "llama_cpp"


class DeviceType(str, Enum):
    CPU = "cpu"
    GPU = "gpu"
    MPS = "mps"
    AUTO = "auto"


@dataclass
class ModelConfig:
    model_id: str
    model_name: str
    model_type: str
    runtime_type: RuntimeType
    device_type: DeviceType = DeviceType.AUTO
    quantization: Optional[str] = None
    max_tokens: int = 512
    batch_size: int = 1
    cache_size: int = 1024
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class GenerationConfig:
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 50
    repetition_penalty: float = 1.0
    stream: bool = False


@dataclass
class GenerationResult:
    text: str
    model_name: str
    tokens_generated: int
    execution_time: float
    metadata: Dict[str, Any] = None


# ============ MOCK RUNTIME ============

class MockModelRuntime:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.is_loaded = False

    async def load(self) -> bool:
        self.is_loaded = True
        return True

    async def unload(self) -> None:
        self.is_loaded = False

    async def generate(self, gen_config: GenerationConfig) -> GenerationResult:
        return GenerationResult(
            text=f"Mock output for: {gen_config.prompt}",
            model_name=self.config.model_name,
            tokens_generated=10,
            execution_time=0.1,
            metadata={"mock": True},
        )

    async def health_check(self):
        return {"status": "mock_healthy"}

    def get_memory_usage(self) -> Dict[str, float]:
        return {"total_mb": 100, "used_mb": 50}


# ============ RUNTIME MANAGER ============

class RuntimeManager:
    def __init__(self):
        self.runtimes: Dict[str, MockModelRuntime] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.loaded_models: Dict[str, MockModelRuntime] = {}

    def register_model(self, config: ModelConfig) -> bool:
        try:
            runtime = self._create_runtime(config)
            self.model_configs[config.model_name] = config
            self.runtimes[config.model_name] = runtime
            return True
        except Exception as e:
            print(f"Error registering model: {e}")
            return False

    def _create_runtime(self, config: ModelConfig) -> MockModelRuntime:
        return MockModelRuntime(config)

    async def load_model(self, model_name: str) -> bool:
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
        if model_name in self.loaded_models:
            runtime = self.loaded_models[model_name]
            await runtime.unload()
            del self.loaded_models[model_name]

    async def generate(self, model_name: str, gen_config: GenerationConfig) -> GenerationResult:
        if model_name not in self.loaded_models:
            await self.load_model(model_name)
        runtime = self.loaded_models[model_name]
        return await runtime.generate(gen_config)

    async def health_check(self) -> Dict[str, Any]:
        health = {
            "status": "healthy",
            "registered_models": len(self.model_configs),
            "loaded_models": len(self.loaded_models),
            "models": {},
        }
        for model_name, runtime in self.loaded_models.items():
            health["models"][model_name] = await runtime.health_check()
        return health

    def list_models(self) -> List[Dict[str, Any]]:
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


# ============ TESTS ============

class TestRuntimeManager:
    """Test RuntimeManager functionality."""

    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = RuntimeManager()
        assert len(manager.runtimes) == 0
        assert len(manager.loaded_models) == 0
        assert len(manager.model_configs) == 0

    def test_register_model(self):
        """Test model registration."""
        manager = RuntimeManager()
        config = ModelConfig(
            model_id="test/model",
            model_name="TestModel",
            model_type="llm",
            runtime_type=RuntimeType.TRANSFORMERS,
        )
        success = manager.register_model(config)
        assert success is True
        assert "TestModel" in manager.model_configs
        assert "TestModel" in manager.runtimes

    @pytest.mark.asyncio
    async def test_load_model(self):
        """Test loading a model."""
        manager = RuntimeManager()
        config = ModelConfig(
            model_id="test/model",
            model_name="TestModel",
            model_type="llm",
            runtime_type=RuntimeType.TRANSFORMERS,
        )
        manager.register_model(config)
        success = await manager.load_model("TestModel")
        assert success is True
        assert "TestModel" in manager.loaded_models
        assert manager.loaded_models["TestModel"].is_loaded is True

    @pytest.mark.asyncio
    async def test_load_nonexistent_model(self):
        """Test loading a model that doesn't exist."""
        manager = RuntimeManager()
        with pytest.raises(ValueError):
            await manager.load_model("NonExistentModel")

    @pytest.mark.asyncio
    async def test_unload_model(self):
        """Test unloading a model."""
        manager = RuntimeManager()
        config = ModelConfig(
            model_id="test/model",
            model_name="TestModel",
            model_type="llm",
            runtime_type=RuntimeType.TRANSFORMERS,
        )
        manager.register_model(config)
        await manager.load_model("TestModel")
        await manager.unload_model("TestModel")
        assert "TestModel" not in manager.loaded_models

    @pytest.mark.asyncio
    async def test_generate(self):
        """Test text generation."""
        manager = RuntimeManager()
        config = ModelConfig(
            model_id="test/model",
            model_name="TestModel",
            model_type="llm",
            runtime_type=RuntimeType.TRANSFORMERS,
        )
        manager.register_model(config)
        gen_config = GenerationConfig(prompt="Hello, world!")
        result = await manager.generate("TestModel", gen_config)
        assert isinstance(result, GenerationResult)
        assert "Hello, world!" in result.text
        assert result.tokens_generated == 10

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check."""
        manager = RuntimeManager()
        config = ModelConfig(
            model_id="test/model",
            model_name="TestModel",
            model_type="llm",
            runtime_type=RuntimeType.TRANSFORMERS,
        )
        manager.register_model(config)
        await manager.load_model("TestModel")
        health = await manager.health_check()
        assert health["status"] == "healthy"
        assert "registered_models" in health
        assert "loaded_models" in health

    def test_list_models(self):
        """Test listing models."""
        manager = RuntimeManager()
        config = ModelConfig(
            model_id="test/model",
            model_name="TestModel",
            model_type="llm",
            runtime_type=RuntimeType.TRANSFORMERS,
        )
        manager.register_model(config)
        models = manager.list_models()
        assert len(models) > 0
        assert any(m["name"] == "TestModel" for m in models)

    def test_get_model_info(self):
        """Test getting model information."""
        manager = RuntimeManager()
        config = ModelConfig(
            model_id="test/model",
            model_name="TestModel",
            model_type="llm",
            runtime_type=RuntimeType.TRANSFORMERS,
            quantization="int8",
        )
        manager.register_model(config)
        info = manager.get_model_info("TestModel")
        assert info is not None
        assert info["name"] == "TestModel"
        assert info["quantization"] == "int8"

    @pytest.mark.asyncio
    async def test_generate_unregistered_model(self):
        """Test generating with a model that is not registered."""
        manager = RuntimeManager()
        gen_config = GenerationConfig(prompt="Test prompt")
        with pytest.raises(ValueError, match="Model NonExistentModel not registered"):
            await manager.generate("NonExistentModel", gen_config)

    @pytest.mark.asyncio
    async def test_concurrent_load_and_generate(self):
        """Test concurrent loading and generation with multiple models."""
        manager = RuntimeManager()
        config1 = ModelConfig(model_id="test/model1", model_name="Model1", model_type="llm", runtime_type=RuntimeType.TRANSFORMERS)
        config2 = ModelConfig(model_id="test/model2", model_name="Model2", model_type="llm", runtime_type=RuntimeType.LLAMA_CPP)
        manager.register_model(config1)
        manager.register_model(config2)

        gen_config1 = GenerationConfig(prompt="Hello from Model1")
        gen_config2 = GenerationConfig(prompt="Hello from Model2")

        tasks = [
            manager.generate("Model1", gen_config1),
            manager.generate("Model2", gen_config2),
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 2
        assert "Model1" in manager.loaded_models
        assert "Model2" in manager.loaded_models
        assert "Mock output for: Hello from Model1" in results[0].text
        assert "Mock output for: Hello from Model2" in results[1].text

    def test_get_model_info_nonexistent(self):
        """Test getting info for a non-existent model."""
        manager = RuntimeManager()
        info = manager.get_model_info("NonExistentModel")
        assert info is None

    @pytest.mark.asyncio
    async def test_unload_non_loaded_model(self):
        """Test that unloading a model that is not loaded does not raise an error."""
        manager = RuntimeManager()
        config = ModelConfig(model_id="test/model", model_name="TestModel", model_type="llm", runtime_type=RuntimeType.TRANSFORMERS)
        manager.register_model(config)
        # Should not raise any exception
        await manager.unload_model("TestModel")
        assert "TestModel" not in manager.loaded_models

    @pytest.mark.asyncio
    async def test_reload_model(self):
        """Test that loading a model that is already loaded returns True without reloading."""
        manager = RuntimeManager()
        config = ModelConfig(model_id="test/model", model_name="TestModel", model_type="llm", runtime_type=RuntimeType.TRANSFORMERS)
        manager.register_model(config)

        # Mock the runtime's load method to check if it's called
        with patch.object(manager.runtimes["TestModel"], 'load', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = True

            # First load
            success1 = await manager.load_model("TestModel")
            assert success1 is True
            assert "TestModel" in manager.loaded_models
            mock_load.assert_called_once()

            # Second load
            success2 = await manager.load_model("TestModel")
            assert success2 is True
            # The load method should not be called again
            mock_load.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_auto_load(self):
        """Test that calling generate on an unloaded model automatically loads it."""
        manager = RuntimeManager()
        config = ModelConfig(model_id="test/model", model_name="TestModel", model_type="llm", runtime_type=RuntimeType.TRANSFORMERS)
        manager.register_model(config)

        assert "TestModel" not in manager.loaded_models

        gen_config = GenerationConfig(prompt="Auto-load test")
        result = await manager.generate("TestModel", gen_config)

        assert "TestModel" in manager.loaded_models
        assert manager.loaded_models["TestModel"].is_loaded is True
        assert "Mock output for: Auto-load test" in result.text



class TestModelConfig:
    """Test ModelConfig."""

    def test_config_creation(self):
        """Test creating a model config."""
        config = ModelConfig(
            model_id="google/gemma-2b",
            model_name="Gemma-2B",
            model_type="llm",
            runtime_type=RuntimeType.TRANSFORMERS,
            device_type=DeviceType.MPS,
            quantization="int8",
        )
        assert config.model_id == "google/gemma-2b"
        assert config.model_name == "Gemma-2B"
        assert config.runtime_type == RuntimeType.TRANSFORMERS
        assert config.device_type == DeviceType.MPS

    def test_config_defaults(self):
        """Test config default values."""
        config = ModelConfig(
            model_id="test/model",
            model_name="Test",
            model_type="llm",
            runtime_type=RuntimeType.TRANSFORMERS,
        )
        assert config.quantization is None
        assert config.max_tokens == 512
        assert config.batch_size == 1
        assert config.device_type == DeviceType.AUTO


class TestGenerationConfig:
    """Test GenerationConfig."""

    def test_generation_config(self):
        """Test creating generation config."""
        config = GenerationConfig(
            prompt="Hello",
            max_tokens=256,
            temperature=0.5,
        )
        assert config.prompt == "Hello"
        assert config.max_tokens == 256
        assert config.temperature == 0.5

    def test_generation_config_defaults(self):
        """Test generation config defaults."""
        config = GenerationConfig(prompt="Hello")
        assert config.max_tokens == 512
        assert config.temperature == 0.7
        assert config.top_p == 0.95


class TestRuntimeTypes:
    """Test RuntimeType and DeviceType enums."""

    def test_runtime_types(self):
        """Test all runtime types."""
        assert RuntimeType.TRANSFORMERS.value == "transformers"
        assert RuntimeType.LLAMA_CPP.value == "llama_cpp"

    def test_device_types(self):
        """Test all device types."""
        assert DeviceType.CPU.value == "cpu"
        assert DeviceType.GPU.value == "gpu"
        assert DeviceType.MPS.value == "mps"
        assert DeviceType.AUTO.value == "auto"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
