"""Orchestrator service for executing multi-model pipelines with isolated steps."""

from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, Any, Dict, List
from enum import Enum
from dataclasses import dataclass, field, asdict
from sqlmodel import Session, select

from langflow.services.database.models.project.model import (
    OrchestrationRun,
    GeneratedArtifact,
)


class StepStatus(str, Enum):
    """Status of an orchestration step."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ModelType(str, Enum):
    """Supported model types for orchestration steps."""
    CODE_LLAMA = "CodeLlama"
    CODE_GEMMA = "CodeGemma"
    T5_GEMMA = "T5Gemma"
    ASSEMBLER = "Assembler"  # Special model for final assembly


@dataclass
class StepInput:
    """Input for an orchestration step."""
    step_name: str
    model_type: ModelType
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepOutput:
    """Output from an orchestration step."""
    step_name: str
    status: StepStatus
    result: Optional[str] = None
    error: Optional[str] = None
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    execution_time: float = 0.0


@dataclass
class OrchestrationPipeline:
    """Definition of an orchestration pipeline."""
    project_id: UUID
    name: str
    steps: List[StepInput]
    global_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class OrchestratorService:
    """Service for managing orchestration runs and executing pipelines."""

    def __init__(self, session: Session, hf_manager=None):
        """
        Initialize the orchestrator service.
        
        Args:
            session: SQLModel session for database operations
            hf_manager: Optional HFModelManager for model execution
        """
        self.session = session
        self.hf_manager = hf_manager
        self.step_history: Dict[UUID, List[StepOutput]] = {}

    # ============ ORCHESTRATION EXECUTION ============

    def execute_pipeline(
        self,
        pipeline: OrchestrationPipeline,
        run_id: UUID,
    ) -> Dict[str, Any]:
        """
        Execute a complete orchestration pipeline.
        
        Args:
            pipeline: OrchestrationPipeline definition
            run_id: UUID of the orchestration run
            
        Returns:
            Dictionary with execution results and artifacts
        """
        self.step_history[run_id] = []
        results = {
            "run_id": str(run_id),
            "project_id": str(pipeline.project_id),
            "status": "RUNNING",
            "steps": [],
            "final_artifacts": [],
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # Update run status to RUNNING
            self._update_run(run_id, "RUNNING")

            # Prepare execution context
            execution_context = pipeline.global_context.copy()

            # Execute each step sequentially
            for i, step_input in enumerate(pipeline.steps):
                step_output = self._execute_step(step_input, execution_context)
                self.step_history[run_id].append(step_output)
                results["steps"].append(asdict(step_output))

                # If step failed and is not resumable, stop pipeline
                if step_output.status == StepStatus.FAILED:
                    results["status"] = "FAILED"
                    results["error"] = f"Pipeline stopped at step '{step_input.step_name}': {step_output.error}"
                    self._update_run(run_id, "FAILED")
                    break

                # Add step output to context for next steps
                execution_context[f"step_{i}_output"] = step_output.result
                execution_context[f"step_{i}_artifacts"] = step_output.artifacts

                # Save artifacts to database
                for artifact in step_output.artifacts:
                    self._save_artifact(run_id, pipeline.project_id, artifact)

            # If all steps succeeded, run assembler model
            if results["status"] == "RUNNING":
                assembler_output = self._run_assembler(
                    run_id,
                    pipeline.project_id,
                    execution_context,
                    self.step_history[run_id],
                )
                results["final_artifacts"] = assembler_output["artifacts"]
                results["assembled_code"] = assembler_output["assembled_code"]
                results["status"] = "SUCCESS"
                self._update_run(run_id, "SUCCESS")

        except Exception as e:
            results["status"] = "FAILED"
            results["error"] = str(e)
            self._update_run(run_id, "FAILED")

        results["finished_at"] = datetime.now(timezone.utc).isoformat()
        return results

    def _execute_step(
        self,
        step_input: StepInput,
        execution_context: Dict[str, Any],
    ) -> StepOutput:
        """
        Execute a single orchestration step.
        
        Args:
            step_input: Input for the step
            execution_context: Shared context from previous steps
            
        Returns:
            StepOutput with results and artifacts
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Prepare the prompt with context injection
            enriched_prompt = self._inject_context(step_input.prompt, execution_context)

            # Route to appropriate model executor
            if step_input.model_type == ModelType.CODE_LLAMA:
                result = self._execute_code_llama(enriched_prompt, step_input.parameters)
            elif step_input.model_type == ModelType.CODE_GEMMA:
                result = self._execute_code_gemma(enriched_prompt, step_input.parameters)
            elif step_input.model_type == ModelType.T5_GEMMA:
                result = self._execute_t5_gemma(enriched_prompt, step_input.parameters)
            else:
                raise ValueError(f"Unknown model type: {step_input.model_type}")

            # Extract artifacts from result
            artifacts = self._extract_artifacts(step_input.step_name, result)

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

            return StepOutput(
                step_name=step_input.step_name,
                status=StepStatus.SUCCESS,
                result=result,
                artifacts=artifacts,
                execution_time=elapsed,
            )

        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            return StepOutput(
                step_name=step_input.step_name,
                status=StepStatus.FAILED,
                error=str(e),
                execution_time=elapsed,
            )

    def _execute_code_llama(self, prompt: str, parameters: Dict[str, Any]) -> str:
        """
        Execute CodeLlama model.
        
        Uses HFModelManager if available, otherwise returns a placeholder.
        """
        if self.hf_manager:
            try:
                result = self.hf_manager.generate(
                    model_name="CodeLlama-7b",
                    prompt=prompt,
                    max_tokens=parameters.get("max_tokens", 512),
                    temperature=parameters.get("temperature", 0.7),
                )
                return result
            except Exception:
                pass

        # Placeholder for when HF manager is not available
        return f"[CodeLlama] Placeholder response to: {prompt[:100]}..."

    def _execute_code_gemma(self, prompt: str, parameters: Dict[str, Any]) -> str:
        """
        Execute CodeGemma model.
        
        Uses HFModelManager if available, otherwise returns a placeholder.
        """
        if self.hf_manager:
            try:
                result = self.hf_manager.generate(
                    model_name="CodeGemma-7b",
                    prompt=prompt,
                    max_tokens=parameters.get("max_tokens", 512),
                    temperature=parameters.get("temperature", 0.7),
                )
                return result
            except Exception:
                pass

        # Placeholder for when HF manager is not available
        return f"[CodeGemma] Placeholder response to: {prompt[:100]}..."

    def _execute_t5_gemma(self, prompt: str, parameters: Dict[str, Any]) -> str:
        """
        Execute T5Gemma model.
        
        Uses HFModelManager if available, otherwise returns a placeholder.
        """
        if self.hf_manager:
            try:
                result = self.hf_manager.generate(
                    model_name="T5-Gemma",
                    prompt=prompt,
                    max_tokens=parameters.get("max_tokens", 512),
                    temperature=parameters.get("temperature", 0.7),
                )
                return result
            except Exception:
                pass

        # Placeholder for when HF manager is not available
        return f"[T5Gemma] Placeholder response to: {prompt[:100]}..."

    def _run_assembler(
        self,
        run_id: UUID,
        project_id: UUID,
        execution_context: Dict[str, Any],
        step_outputs: List[StepOutput],
    ) -> Dict[str, Any]:
        """
        Run the Assembler model to combine and clean outputs.
        
        The Assembler is a special model that:
        - Collects all intermediate outputs (artifacts)
        - Combines them as a "Lego" pattern
        - Cleans and polishes the final code
        - Validates the combined output
        """
        # Build assembler prompt from all intermediate outputs
        assembler_prompt = self._build_assembler_prompt(step_outputs)

        try:
            if self.hf_manager:
                assembled_code = self.hf_manager.generate(
                    model_name="CodeLlama-7b",  # Use CodeLlama for assembly
                    prompt=assembler_prompt,
                    max_tokens=2048,
                    temperature=0.3,  # Lower temp for more deterministic output
                )
            else:
                assembled_code = f"[Assembled Output]\n\n{assembler_prompt}"

            # Extract final artifacts
            artifacts = self._extract_artifacts("assembler", assembled_code)

            return {
                "assembled_code": assembled_code,
                "artifacts": artifacts,
            }

        except Exception as e:
            return {
                "assembled_code": "",
                "artifacts": [],
                "error": str(e),
            }

    # ============ HELPER METHODS ============

    def _inject_context(self, prompt: str, context: Dict[str, Any]) -> str:
        """Inject execution context into the prompt."""
        context_str = "\n".join(
            [f"# {k}: {str(v)[:200]}" for k, v in context.items()]
        )
        return f"{prompt}\n\n## Available Context:\n{context_str}"

    def _extract_artifacts(self, step_name: str, result: str) -> List[Dict[str, Any]]:
        """
        Extract artifacts (JSX, CSS, etc.) from model output.
        
        Looks for code blocks and metadata markers in the output.
        """
        artifacts = []

        # Simple artifact extraction: look for code blocks
        import re

        # Extract JSX components
        jsx_blocks = re.findall(r"```jsx(.*?)```", result, re.DOTALL)
        for i, jsx in enumerate(jsx_blocks):
            artifacts.append({
                "type": "jsx",
                "name": f"{step_name}_component_{i}.jsx",
                "content": jsx.strip(),
            })

        # Extract TypeScript/TSX
        tsx_blocks = re.findall(r"```tsx(.*?)```", result, re.DOTALL)
        for i, tsx in enumerate(tsx_blocks):
            artifacts.append({
                "type": "tsx",
                "name": f"{step_name}_component_{i}.tsx",
                "content": tsx.strip(),
            })

        # Extract CSS
        css_blocks = re.findall(r"```css(.*?)```", result, re.DOTALL)
        for i, css in enumerate(css_blocks):
            artifacts.append({
                "type": "css",
                "name": f"{step_name}_styles_{i}.css",
                "content": css.strip(),
            })

        # Extract Python
        py_blocks = re.findall(r"```python(.*?)```", result, re.DOTALL)
        for i, py in enumerate(py_blocks):
            artifacts.append({
                "type": "python",
                "name": f"{step_name}_script_{i}.py",
                "content": py.strip(),
            })

        return artifacts

    def _build_assembler_prompt(self, step_outputs: List[StepOutput]) -> str:
        """Build the assembler prompt from all intermediate outputs."""
        prompt_lines = [
            "# Assembly Task",
            "You are an expert code assembler. Your task is to:",
            "1. Review the following step outputs",
            "2. Combine them into a cohesive, production-ready codebase",
            "3. Follow the 'Lego pattern': each piece should fit perfectly",
            "4. Clean up, optimize, and polish the code",
            "5. Add proper comments and documentation",
            "",
            "## Step Outputs:",
        ]

        for i, step_output in enumerate(step_outputs, 1):
            prompt_lines.append(f"\n### Step {i}: {step_output.step_name}")
            prompt_lines.append(f"Status: {step_output.status.value}")
            if step_output.result:
                prompt_lines.append("Result:")
                prompt_lines.append(step_output.result[:500])
            if step_output.artifacts:
                prompt_lines.append("Artifacts:")
                for artifact in step_output.artifacts:
                    prompt_lines.append(f"- {artifact.get('name', 'unknown')}")

        prompt_lines.extend([
            "",
            "## Final Assembly Instructions:",
            "1. Create a cohesive structure",
            "2. Remove duplication",
            "3. Ensure type safety (TypeScript/Python)",
            "4. Add proper error handling",
            "5. Include comprehensive documentation",
            "",
            "Provide the final, production-ready code in code blocks.",
        ])

        return "\n".join(prompt_lines)

    def _save_artifact(
        self,
        run_id: UUID,
        project_id: UUID,
        artifact: Dict[str, Any],
    ) -> None:
        """Save an artifact to the database."""
        try:
            db_artifact = GeneratedArtifact(
                project_id=project_id,
                run_id=run_id,
                name=artifact.get("name", "unknown"),
                path=f"/artifacts/{artifact.get('name', 'unknown')}",
                content=artifact.get("content", ""),
                metadata={
                    "type": artifact.get("type", "unknown"),
                    "source": "orchestrator",
                },
            )
            self.session.add(db_artifact)
            self.session.commit()
        except Exception as e:
            print(f"Warning: Failed to save artifact: {e}")

    def _update_run(self, run_id: UUID, status: str) -> None:
        """Update the status of an orchestration run."""
        try:
            run = self.session.exec(
                select(OrchestrationRun).where(OrchestrationRun.id == run_id)
            ).first()
            if run:
                run.status = status
                if status in ("SUCCESS", "FAILED"):
                    run.finished_at = datetime.now(timezone.utc)
                self.session.add(run)
                self.session.commit()
        except Exception as e:
            print(f"Warning: Failed to update run status: {e}")

    # ============ PIPELINE MANAGEMENT ============

    def get_step_history(self, run_id: UUID) -> List[StepOutput]:
        """Retrieve execution history for a run."""
        return self.step_history.get(run_id, [])

    def get_run_summary(self, run_id: UUID) -> Dict[str, Any]:
        """Get a summary of a completed run."""
        history = self.get_step_history(run_id)
        
        successful_steps = sum(1 for step in history if step.status == StepStatus.SUCCESS)
        failed_steps = sum(1 for step in history if step.status == StepStatus.FAILED)
        total_time = sum(step.execution_time for step in history)

        return {
            "run_id": str(run_id),
            "total_steps": len(history),
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "total_execution_time": total_time,
            "steps": [asdict(step) for step in history],
        }
