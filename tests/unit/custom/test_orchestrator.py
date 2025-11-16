"""Unit tests for Orchestrator service."""

import pytest
from uuid import uuid4
from datetime import datetime
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from typing import Optional

from langflow.custom.orchestrator.service import (
    OrchestratorService,
    OrchestrationPipeline,
    StepInput,
    ModelType,
    StepStatus,
)


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="orchestrator")
def orchestrator_fixture(session: Session):
    """Create an OrchestratorService instance for testing."""
    return OrchestratorService(session)


@pytest.fixture(name="test_project_id")
def test_project_id_fixture():
    """Create a test project ID."""
    return uuid4()


class TestStepExecution:
    """Test individual step execution."""

    def test_execute_code_llama_step(self, orchestrator: OrchestratorService):
        """Test executing a CodeLlama step."""
        step_input = StepInput(
            step_name="generate_code",
            model_type=ModelType.CODE_LLAMA,
            prompt="Generate a simple React component",
            context={"framework": "react"},
            parameters={"max_tokens": 512, "temperature": 0.7},
        )

        output = orchestrator._execute_step(step_input, {})

        assert output.step_name == "generate_code"
        assert output.status == StepStatus.SUCCESS
        assert output.result is not None
        assert output.execution_time >= 0

    def test_execute_code_gemma_step(self, orchestrator: OrchestratorService):
        """Test executing a CodeGemma step."""
        step_input = StepInput(
            step_name="refine_code",
            model_type=ModelType.CODE_GEMMA,
            prompt="Refine and optimize the code",
            context={"quality": "high"},
        )

        output = orchestrator._execute_step(step_input, {})

        assert output.step_name == "refine_code"
        assert output.status == StepStatus.SUCCESS

    def test_execute_t5_gemma_step(self, orchestrator: OrchestratorService):
        """Test executing a T5Gemma step."""
        step_input = StepInput(
            step_name="transform_code",
            model_type=ModelType.T5_GEMMA,
            prompt="Transform the code structure",
        )

        output = orchestrator._execute_step(step_input, {})

        assert output.step_name == "transform_code"
        assert output.status == StepStatus.SUCCESS

    def test_step_failure_handling(self, orchestrator: OrchestratorService):
        """Test handling of failed steps."""
        step_input = StepInput(
            step_name="will_fail",
            model_type=ModelType(999),  # Invalid model type
            prompt="This should fail",
        )

        output = orchestrator._execute_step(step_input, {})

        assert output.status == StepStatus.FAILED
        assert output.error is not None


class TestContextInjection:
    """Test context injection into prompts."""

    def test_inject_context_empty(self, orchestrator: OrchestratorService):
        """Test context injection with empty context."""
        prompt = "Generate code"
        result = orchestrator._inject_context(prompt, {})

        assert prompt in result
        assert "Available Context" in result

    def test_inject_context_with_data(self, orchestrator: OrchestratorService):
        """Test context injection with actual context."""
        prompt = "Generate code"
        context = {
            "framework": "React",
            "version": "18.0",
        }
        result = orchestrator._inject_context(prompt, context)

        assert prompt in result
        assert "framework" in result
        assert "React" in result


class TestArtifactExtraction:
    """Test artifact extraction from model outputs."""

    def test_extract_jsx_artifacts(self, orchestrator: OrchestratorService):
        """Test extracting JSX from output."""
        result = """
        Here's a React component:
        
        ```jsx
        export default function MyComponent() {
            return <div>Hello World</div>;
        }
        ```
        """

        artifacts = orchestrator._extract_artifacts("test_step", result)

        assert len(artifacts) > 0
        assert any(a["type"] == "jsx" for a in artifacts)
        assert any("export default" in a["content"] for a in artifacts)

    def test_extract_css_artifacts(self, orchestrator: OrchestratorService):
        """Test extracting CSS from output."""
        result = """
        Here's the styling:
        
        ```css
        .component {
            color: blue;
            padding: 10px;
        }
        ```
        """

        artifacts = orchestrator._extract_artifacts("test_step", result)

        assert any(a["type"] == "css" for a in artifacts)

    def test_extract_python_artifacts(self, orchestrator: OrchestratorService):
        """Test extracting Python code from output."""
        result = """
        Python implementation:
        
        ```python
        def hello():
            print("Hello World")
        ```
        """

        artifacts = orchestrator._extract_artifacts("test_step", result)

        assert any(a["type"] == "python" for a in artifacts)

    def test_extract_multiple_artifacts(self, orchestrator: OrchestratorService):
        """Test extracting multiple artifacts of different types."""
        result = """
        ```jsx
        export default function App() {}
        ```
        
        ```css
        .app { display: flex; }
        ```
        
        ```jsx
        function Button() { return <button>Click</button>; }
        ```
        """

        artifacts = orchestrator._extract_artifacts("test_step", result)

        assert len(artifacts) >= 3
        jsx_artifacts = [a for a in artifacts if a["type"] == "jsx"]
        css_artifacts = [a for a in artifacts if a["type"] == "css"]
        assert len(jsx_artifacts) >= 2
        assert len(css_artifacts) >= 1


class TestAssemblerPromptBuilding:
    """Test assembler prompt construction."""

    def test_build_assembler_prompt(
        self,
        orchestrator: OrchestratorService,
    ):
        """Test building assembler prompt from step outputs."""
        from langflow.custom.orchestrator.service import StepOutput

        step_outputs = [
            StepOutput(
                step_name="step_1",
                status=StepStatus.SUCCESS,
                result="Generated component code",
                artifacts=[{"name": "component.jsx", "type": "jsx"}],
            ),
            StepOutput(
                step_name="step_2",
                status=StepStatus.SUCCESS,
                result="Generated CSS",
                artifacts=[{"name": "styles.css", "type": "css"}],
            ),
        ]

        prompt = orchestrator._build_assembler_prompt(step_outputs)

        assert "Assembly Task" in prompt
        assert "step_1" in prompt
        assert "step_2" in prompt
        assert "component.jsx" in prompt
        assert "styles.css" in prompt


class TestPipelineExecution:
    """Test full pipeline execution."""

    def test_execute_simple_pipeline(
        self,
        orchestrator: OrchestratorService,
        test_project_id: uuid4,
    ):
        """Test executing a simple two-step pipeline."""
        run_id = uuid4()

        steps = [
            StepInput(
                step_name="analyze",
                model_type=ModelType.CODE_LLAMA,
                prompt="Analyze requirements",
            ),
            StepInput(
                step_name="generate",
                model_type=ModelType.CODE_GEMMA,
                prompt="Generate code",
            ),
        ]

        pipeline = OrchestrationPipeline(
            project_id=test_project_id,
            name="Test Pipeline",
            steps=steps,
        )

        result = orchestrator.execute_pipeline(pipeline, run_id)

        assert result["status"] in ("SUCCESS", "FAILED")
        assert "started_at" in result
        assert "finished_at" in result
        assert len(result["steps"]) > 0

    def test_get_step_history(
        self,
        orchestrator: OrchestratorService,
        test_project_id: uuid4,
    ):
        """Test retrieving step history."""
        run_id = uuid4()

        steps = [
            StepInput(
                step_name="step_1",
                model_type=ModelType.CODE_LLAMA,
                prompt="Generate",
            ),
        ]

        pipeline = OrchestrationPipeline(
            project_id=test_project_id,
            name="Test",
            steps=steps,
        )

        orchestrator.execute_pipeline(pipeline, run_id)
        history = orchestrator.get_step_history(run_id)

        assert len(history) > 0
        assert history[0].step_name == "step_1"

    def test_get_run_summary(
        self,
        orchestrator: OrchestratorService,
        test_project_id: uuid4,
    ):
        """Test retrieving run summary."""
        run_id = uuid4()

        steps = [
            StepInput(
                step_name="step_1",
                model_type=ModelType.CODE_LLAMA,
                prompt="Generate",
            ),
        ]

        pipeline = OrchestrationPipeline(
            project_id=test_project_id,
            name="Test",
            steps=steps,
        )

        orchestrator.execute_pipeline(pipeline, run_id)
        summary = orchestrator.get_run_summary(run_id)

        assert summary["total_steps"] > 0
        assert "successful_steps" in summary
        assert "failed_steps" in summary
        assert "total_execution_time" in summary
