"""Simplified unit tests for Orchestrator service (no Langflow dependencies)."""

import pytest
from uuid import uuid4
from dataclasses import dataclass, asdict


class StepStatusTest:
    """Status options for steps."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ModelTypeTest:
    """Supported model types."""
    CODE_LLAMA = "CodeLlama"
    CODE_GEMMA = "CodeGemma"
    T5_GEMMA = "T5Gemma"
    ASSEMBLER = "Assembler"


@dataclass
class StepOutputTest:
    """Output from an orchestration step."""
    step_name: str
    status: str
    result: str = None
    error: str = None
    artifacts: list = None
    execution_time: float = 0.0

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


class OrchestratorServiceTest:
    """Simplified orchestrator for testing."""

    def __init__(self):
        self.step_history = {}

    def _execute_step(self, step_name: str, model_type: str, prompt: str) -> StepOutputTest:
        """Execute a single step."""
        try:
            result = f"[{model_type}] Generated response to: {prompt[:50]}..."
            artifacts = self._extract_artifacts(step_name, result)
            return StepOutputTest(
                step_name=step_name,
                status=StepStatusTest.SUCCESS,
                result=result,
                artifacts=artifacts,
                execution_time=0.1,
            )
        except Exception as e:
            return StepOutputTest(
                step_name=step_name,
                status=StepStatusTest.FAILED,
                error=str(e),
            )

    def _extract_artifacts(self, step_name: str, result: str) -> list:
        """Extract artifacts from result."""
        import re

        artifacts = []

        jsx_blocks = re.findall(r"```jsx(.*?)```", result, re.DOTALL)
        for i, jsx in enumerate(jsx_blocks):
            artifacts.append({
                "type": "jsx",
                "name": f"{step_name}_component_{i}.jsx",
                "content": jsx.strip(),
            })

        css_blocks = re.findall(r"```css(.*?)```", result, re.DOTALL)
        for i, css in enumerate(css_blocks):
            artifacts.append({
                "type": "css",
                "name": f"{step_name}_styles_{i}.css",
                "content": css.strip(),
            })

        py_blocks = re.findall(r"```python(.*?)```", result, re.DOTALL)
        for i, py in enumerate(py_blocks):
            artifacts.append({
                "type": "python",
                "name": f"{step_name}_script_{i}.py",
                "content": py.strip(),
            })

        return artifacts

    def _inject_context(self, prompt: str, context: dict) -> str:
        """Inject context into prompt."""
        context_str = "\n".join(
            [f"# {k}: {str(v)[:100]}" for k, v in context.items()]
        )
        return f"{prompt}\n\n## Context:\n{context_str}"

    def _build_assembler_prompt(self, step_outputs: list) -> str:
        """Build assembler prompt."""
        lines = [
            "# Assembly Task",
            "Combine the following outputs into production code:",
            "",
        ]

        for i, step_output in enumerate(step_outputs, 1):
            lines.append(f"### Step {i}: {step_output.step_name}")
            if step_output.result:
                lines.append(step_output.result[:200])
            for artifact in step_output.artifacts:
                lines.append(f"- {artifact['name']}")

        return "\n".join(lines)

    def execute_pipeline(self, project_id: str, steps: list, run_id: str) -> dict:
        """Execute a pipeline."""
        self.step_history[run_id] = []
        results = {
            "run_id": run_id,
            "project_id": project_id,
            "status": "RUNNING",
            "steps": [],
        }

        try:
            execution_context = {}

            for i, step in enumerate(steps):
                output = self._execute_step(
                    step["step_name"],
                    step["model_type"],
                    step["prompt"],
                )
                self.step_history[run_id].append(output)
                results["steps"].append(asdict(output))

                if output.status == StepStatusTest.FAILED:
                    results["status"] = "FAILED"
                    break

                execution_context[f"step_{i}"] = output.result

            if results["status"] == "RUNNING":
                results["status"] = "SUCCESS"

        except Exception as e:
            results["status"] = "FAILED"
            results["error"] = str(e)

        return results

    def get_run_summary(self, run_id: str) -> dict:
        """Get run summary."""
        history = self.step_history.get(run_id, [])
        successful = sum(1 for s in history if s.status == StepStatusTest.SUCCESS)
        failed = sum(1 for s in history if s.status == StepStatusTest.FAILED)
        total_time = sum(s.execution_time for s in history)

        return {
            "run_id": run_id,
            "total_steps": len(history),
            "successful_steps": successful,
            "failed_steps": failed,
            "total_execution_time": total_time,
        }


# ============ TESTS ============


class TestOrchestratorStepExecution:
    """Test step execution."""

    def test_execute_code_llama_step(self):
        """Test executing CodeLlama step."""
        orchestrator = OrchestratorServiceTest()
        output = orchestrator._execute_step(
            "generate",
            ModelTypeTest.CODE_LLAMA,
            "Generate a React component",
        )

        assert output.step_name == "generate"
        assert output.status == StepStatusTest.SUCCESS
        assert output.result is not None

    def test_execute_code_gemma_step(self):
        """Test executing CodeGemma step."""
        orchestrator = OrchestratorServiceTest()
        output = orchestrator._execute_step(
            "refine",
            ModelTypeTest.CODE_GEMMA,
            "Refine the code",
        )

        assert output.status == StepStatusTest.SUCCESS

    def test_execute_t5_gemma_step(self):
        """Test executing T5Gemma step."""
        orchestrator = OrchestratorServiceTest()
        output = orchestrator._execute_step(
            "transform",
            ModelTypeTest.T5_GEMMA,
            "Transform the code",
        )

        assert output.status == StepStatusTest.SUCCESS


class TestArtifactExtraction:
    """Test artifact extraction."""

    def test_extract_jsx(self):
        """Test extracting JSX."""
        orchestrator = OrchestratorServiceTest()
        result = """
        ```jsx
        export default function App() {
            return <div>Hello</div>;
        }
        ```
        """

        artifacts = orchestrator._extract_artifacts("test", result)

        assert len(artifacts) > 0
        assert any(a["type"] == "jsx" for a in artifacts)

    def test_extract_css(self):
        """Test extracting CSS."""
        orchestrator = OrchestratorServiceTest()
        result = """
        ```css
        .app { color: blue; }
        ```
        """

        artifacts = orchestrator._extract_artifacts("test", result)

        assert any(a["type"] == "css" for a in artifacts)

    def test_extract_python(self):
        """Test extracting Python."""
        orchestrator = OrchestratorServiceTest()
        result = """
        ```python
        def hello():
            print("Hello")
        ```
        """

        artifacts = orchestrator._extract_artifacts("test", result)

        assert any(a["type"] == "python" for a in artifacts)

    def test_extract_multiple(self):
        """Test extracting multiple artifacts."""
        orchestrator = OrchestratorServiceTest()
        result = """
        ```jsx
        export default function App() {}
        ```
        
        ```css
        .app { display: flex; }
        ```
        """

        artifacts = orchestrator._extract_artifacts("test", result)

        assert len(artifacts) >= 2


class TestContextInjection:
    """Test context injection."""

    def test_inject_context(self):
        """Test injecting context."""
        orchestrator = OrchestratorServiceTest()
        prompt = "Generate code"
        context = {"framework": "react", "version": "18"}

        result = orchestrator._inject_context(prompt, context)

        assert prompt in result
        assert "framework" in result
        assert "react" in result


class TestAssemblerPrompt:
    """Test assembler prompt building."""

    def test_build_assembler_prompt(self):
        """Test building assembler prompt."""
        orchestrator = OrchestratorServiceTest()
        outputs = [
            StepOutputTest(
                step_name="step_1",
                status=StepStatusTest.SUCCESS,
                result="Generated component",
                artifacts=[{"name": "component.jsx"}],
            ),
            StepOutputTest(
                step_name="step_2",
                status=StepStatusTest.SUCCESS,
                result="Generated styles",
                artifacts=[{"name": "styles.css"}],
            ),
        ]

        prompt = orchestrator._build_assembler_prompt(outputs)

        assert "Assembly Task" in prompt
        assert "step_1" in prompt
        assert "component.jsx" in prompt


class TestPipelineExecution:
    """Test pipeline execution."""

    def test_execute_simple_pipeline(self):
        """Test executing simple pipeline."""
        orchestrator = OrchestratorServiceTest()
        run_id = str(uuid4())
        project_id = str(uuid4())

        steps = [
            {
                "step_name": "analyze",
                "model_type": ModelTypeTest.CODE_LLAMA,
                "prompt": "Analyze requirements",
            },
            {
                "step_name": "generate",
                "model_type": ModelTypeTest.CODE_GEMMA,
                "prompt": "Generate code",
            },
        ]

        result = orchestrator.execute_pipeline(project_id, steps, run_id)

        assert result["status"] == "SUCCESS"
        assert len(result["steps"]) == 2

    def test_get_run_summary(self):
        """Test getting run summary."""
        orchestrator = OrchestratorServiceTest()
        run_id = str(uuid4())
        project_id = str(uuid4())

        steps = [
            {
                "step_name": "step_1",
                "model_type": ModelTypeTest.CODE_LLAMA,
                "prompt": "Generate",
            },
        ]

        orchestrator.execute_pipeline(project_id, steps, run_id)
        summary = orchestrator.get_run_summary(run_id)

        assert summary["total_steps"] == 1
        assert summary["successful_steps"] == 1
        assert summary["failed_steps"] == 0
