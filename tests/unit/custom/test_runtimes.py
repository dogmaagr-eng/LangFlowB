"""
Tests for Local Model Runtimes
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Setup path for imports
project_root = Path(__file__).parent.parent.parent.parent
backend_path = project_root / "src" / "backend" / "base"
sys.path.insert(0, str(backend_path))

from langflow.custom.runtimes.manager import (
    RuntimeManager,
    ModelConfig,
    GenerationConfig,
    GenerationResult,
    RuntimeType,
    DeviceType,
    ModelRuntime,
    TransformersRuntime,
    LlamaCppRuntime,
    get_default_models,
)


# ============ MOCK RUNTIME FOR TESTING ============

class MockModelRuntime(ModelRuntime):
    """Mock runtime for testing."""

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


# ============ MANAGER TESTS ============

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

        # Patch create_runtime to return mock
        with patch.object(manager, "_create_runtime", return_value=MockModelRuntime(config)):
            success = manager.register_model(config)

        assert success is True
        assert "TestModel" in manager.model_configs
        assert "TestModel" in manager.runtimes

    def test_get_default_models(self):
        """Test default model configurations."""
        models = get_default_models()
        assert len(models) > 0
        assert all(isinstance(m, ModelConfig) for m in models)
        assert any("gemma" in m.model_id.lower() for m in models)
        assert any("codellama" in m.model_id.lower() for m in models)

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

        mock_runtime = MockModelRuntime(config)
        manager.runtimes["TestModel"] = mock_runtime

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

        mock_runtime = MockModelRuntime(config)
        manager.loaded_models["TestModel"] = mock_runtime
        mock_runtime.is_loaded = True

        await manager.unload_model("TestModel")

        assert "TestModel" not in manager.loaded_models
        assert mock_runtime.is_loaded is False

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

        mock_runtime = MockModelRuntime(config)
        manager.runtimes["TestModel"] = mock_runtime
        manager.model_configs["TestModel"] = config

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

        mock_runtime = MockModelRuntime(config)
        manager.model_configs["TestModel"] = config
        manager.loaded_models["TestModel"] = mock_runtime

        health = await manager.health_check()

        assert health["status"] is not None
        assert "registered_models" in health
        assert "loaded_models" in health
        assert "models" in health

    def test_list_models(self):
        """Test listing models."""
        manager = RuntimeManager()
        config = ModelConfig(
            model_id="test/model",
            model_name="TestModel",
            model_type="llm",
            runtime_type=RuntimeType.TRANSFORMERS,
        )

        with patch.object(manager, "_create_runtime", return_value=MockModelRuntime(config)):
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

        with patch.object(manager, "_create_runtime", return_value=MockModelRuntime(config)):
            manager.register_model(config)

        info = manager.get_model_info("TestModel")

        assert info is not None
        assert info["name"] == "TestModel"
        assert info["quantization"] == "int8"


# ============ MODEL CONFIG TESTS ============

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


# ============ GENERATION CONFIG TESTS ============

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


# ============ RUNTIME TYPE TESTS ============

class TestRuntimeTypes:
    """Test RuntimeType and DeviceType enums."""

    def test_runtime_types(self):
        """Test all runtime types."""
        assert RuntimeType.TRANSFORMERS.value == "transformers"
        assert RuntimeType.LLAMA_CPP.value == "llama_cpp"
        assert RuntimeType.OLLAMA.value == "ollama"

    def test_device_types(self):
        """Test all device types."""
        assert DeviceType.CPU.value == "cpu"
        assert DeviceType.GPU.value == "gpu"
        assert DeviceType.MPS.value == "mps"
        assert DeviceType.AUTO.value == "auto"


# ============ TRANSFORMERS RUNTIME TESTS ============

class TestTransformersRuntime:
    """Test TransformersRuntime."""

    def test_initialization(self):
        """Test TransformersRuntime initialization."""
        config = ModelConfig(
            model_id="test/model",
            model_name="Test",
            model_type="llm",
            runtime_type=RuntimeType.TRANSFORMERS,
        )

        runtime = TransformersRuntime(config)

        assert runtime.config == config
        assert runtime.model is None
        assert runtime.tokenizer is None
        assert runtime.is_loaded is False


# ============ LLAMA.CPP RUNTIME TESTS ============

class TestLlamaCppRuntime:
    """Test LlamaCppRuntime."""

    def test_initialization(self):
        """Test LlamaCppRuntime initialization."""
        config = ModelConfig(
            model_id="./models/model.gguf",
            model_name="Test",
            model_type="llm",
            runtime_type=RuntimeType.LLAMA_CPP,
        )

        runtime = LlamaCppRuntime(config)

        assert runtime.config == config
        assert runtime.model is None
        assert runtime.is_loaded is False


# ============ GENERATION RESULT TESTS ============

class TestGenerationResult:
    """Test GenerationResult."""

    def test_result_creation(self):
        """Test creating a generation result."""
        result = GenerationResult(
            text="Generated text",
            model_name="TestModel",
            tokens_generated=42,
            execution_time=1.5,
        )

        assert result.text == "Generated text"
        assert result.model_name == "TestModel"
        assert result.tokens_generated == 42
        assert result.execution_time == 1.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
