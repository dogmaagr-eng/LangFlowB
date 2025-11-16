"""Framer Component Generator Service.

Transforms JSX/TSX artifacts into Framer-compatible interactive components.
Handles component conversion, property binding, animation setup, and export generation.
"""

import re
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, Any, Dict, List, Tuple
from enum import Enum
from dataclasses import dataclass, field
from sqlmodel import Session, select

from langflow.services.database.models.project.model import (
    GeneratedArtifact,
    OrchestrationRun,
)


class ComponentType(str, Enum):
    """Types of Framer-compatible components."""
    BUTTON = "Button"
    INPUT = "Input"
    CARD = "Card"
    LAYOUT = "Layout"
    INTERACTIVE = "Interactive"
    ANIMATED = "Animated"
    CUSTOM = "Custom"


class AnimationType(str, Enum):
    """Animation types for Framer components."""
    FADE = "fade"
    SCALE = "scale"
    SLIDE = "slide"
    ROTATE = "rotate"
    BOUNCE = "bounce"
    NONE = "none"


@dataclass
class FramerProperty:
    """Property binding for Framer components."""
    name: str
    type: str  # "string", "number", "boolean", "color", etc.
    default_value: Any = None
    description: str = ""
    controls: str = "input"  # "input", "toggle", "colorControl", "select", etc.


@dataclass
class FramerComponent:
    """Framer component definition."""
    name: str
    component_type: ComponentType
    jsx_code: str
    props: List[FramerProperty] = field(default_factory=list)
    animations: Dict[str, AnimationType] = field(default_factory=dict)
    imports: List[str] = field(default_factory=list)
    custom_hooks: List[str] = field(default_factory=list)
    css_modules: Optional[str] = None
    preview_code: Optional[str] = None
    canvas_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FramerExportResult:
    """Result of Framer component generation."""
    run_id: UUID
    component_id: str
    component_name: str
    framer_code: str
    canvas_config: Dict[str, Any]
    animations_config: Dict[str, Any]
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    generation_time: float = 0.0
    status: str = "SUCCESS"
    error: Optional[str] = None


class FramerComponentGenerator:
    """Service for converting components to Framer-compatible format."""

    def __init__(self, session: Session):
        """
        Initialize Framer component generator.
        
        Args:
            session: SQLModel session for database operations
        """
        self.session = session
        self.default_animations = {
            "onTap": AnimationType.SCALE,
            "onHover": AnimationType.FADE,
            "onLoad": AnimationType.FADE,
        }

    # ============ MAIN CONVERSION ============

    def convert_artifacts_to_framer(
        self,
        run_id: UUID,
        artifacts: List[Dict[str, Any]],
        project_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[FramerExportResult]:
        """
        Convert orchestrator artifacts to Framer components.
        
        Args:
            run_id: UUID of the orchestration run
            artifacts: List of artifacts from orchestrator
            project_metadata: Optional project-level configuration
            
        Returns:
            List of FramerExportResult objects
        """
        start_time = datetime.now(timezone.utc)
        results = []

        try:
            for artifact in artifacts:
                if artifact.get("type") not in ["jsx", "tsx"]:
                    continue

                result = self._process_single_artifact(
                    run_id=run_id,
                    artifact=artifact,
                    project_metadata=project_metadata or {},
                )
                results.append(result)

            return results

        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            return [FramerExportResult(
                run_id=run_id,
                component_id="error",
                component_name="Error",
                framer_code="",
                canvas_config={},
                animations_config={},
                status="FAILED",
                error=str(e),
                generation_time=elapsed,
            )]

    def _process_single_artifact(
        self,
        run_id: UUID,
        artifact: Dict[str, Any],
        project_metadata: Dict[str, Any],
    ) -> FramerExportResult:
        """
        Process a single JSX/TSX artifact.
        
        Args:
            run_id: UUID of the run
            artifact: Single artifact dict
            project_metadata: Project-level config
            
        Returns:
            FramerExportResult
        """
        start_time = datetime.now(timezone.utc)

        try:
            component_name = artifact.get("name", "Component").replace(".jsx", "").replace(".tsx", "")
            jsx_code = artifact.get("content", "")

            # Parse component structure
            component = self._parse_component(component_name, jsx_code)

            # Extract props and create bindings
            props = self._extract_props(jsx_code)

            # Detect interactive elements
            interactive_elements = self._find_interactive_elements(jsx_code)

            # Add Framer-specific event handlers
            enhanced_jsx = self._add_framer_events(jsx_code, interactive_elements)

            # Generate Framer wrapper code
            framer_code = self._generate_framer_wrapper(
                component_name=component_name,
                jsx_code=enhanced_jsx,
                props=props,
            )

            # Generate canvas configuration
            canvas_config = self._generate_canvas_config(
                component_name=component_name,
                props=props,
                project_metadata=project_metadata,
            )

            # Generate animations configuration
            animations_config = self._generate_animations_config(interactive_elements)

            # Create secondary artifacts (CSS, hooks, etc.)
            secondary_artifacts = self._generate_secondary_artifacts(component_name, jsx_code)

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

            return FramerExportResult(
                run_id=run_id,
                component_id=component_name.lower(),
                component_name=component_name,
                framer_code=framer_code,
                canvas_config=canvas_config,
                animations_config=animations_config,
                artifacts=secondary_artifacts,
                generation_time=elapsed,
                status="SUCCESS",
            )

        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            return FramerExportResult(
                run_id=run_id,
                component_id=artifact.get("name", "error"),
                component_name=artifact.get("name", "Error"),
                framer_code="",
                canvas_config={},
                animations_config={},
                status="FAILED",
                error=str(e),
                generation_time=elapsed,
            )

    # ============ COMPONENT PARSING ============

    def _parse_component(self, name: str, jsx_code: str) -> FramerComponent:
        """
        Parse JSX code to extract component structure.
        
        Args:
            name: Component name
            jsx_code: JSX code content
            
        Returns:
            FramerComponent object
        """
        # Detect component type
        component_type = self._detect_component_type(jsx_code)

        # Extract imports
        imports = self._extract_imports(jsx_code)

        # Extract custom hooks
        custom_hooks = self._extract_custom_hooks(jsx_code)

        return FramerComponent(
            name=name,
            component_type=component_type,
            jsx_code=jsx_code,
            imports=imports,
            custom_hooks=custom_hooks,
        )

    def _detect_component_type(self, jsx_code: str) -> ComponentType:
        """Detect the primary component type."""
        jsx_lower = jsx_code.lower()

        if "button" in jsx_lower:
            return ComponentType.BUTTON
        elif "input" in jsx_lower or "textinput" in jsx_lower:
            return ComponentType.INPUT
        elif "card" in jsx_lower:
            return ComponentType.CARD
        elif "flex" in jsx_lower or "grid" in jsx_lower or "div" in jsx_lower:
            return ComponentType.LAYOUT
        elif "animation" in jsx_lower or "motion" in jsx_lower:
            return ComponentType.ANIMATED
        elif "onclick" in jsx_lower or "onchange" in jsx_lower or "onsubmit" in jsx_lower:
            return ComponentType.INTERACTIVE
        else:
            return ComponentType.CUSTOM

    def _extract_imports(self, jsx_code: str) -> List[str]:
        """Extract import statements from JSX."""
        import_pattern = r"^import\s+.*?from\s+['\"].*?['\"];?$"
        imports = re.findall(import_pattern, jsx_code, re.MULTILINE)
        return imports or []

    def _extract_custom_hooks(self, jsx_code: str) -> List[str]:
        """Extract custom hook definitions."""
        hook_pattern = r"^(const\s+\w+\s*=\s*\([^)]*\)\s*=>|function\s+\w+\s*\([^)]*\))"
        hooks = re.findall(hook_pattern, jsx_code, re.MULTILINE)
        return hooks or []

    # ============ PROPS EXTRACTION ============

    def _extract_props(self, jsx_code: str) -> List[FramerProperty]:
        """Extract component props from JSX code."""
        props = []

        # Look for function parameters
        func_match = re.search(r"(?:function|const\s+\w+\s*=\s*\()\s*\{([^}]*)\}", jsx_code)
        if func_match:
            props_str = func_match.group(1)
            for prop in props_str.split(","):
                prop = prop.strip()
                if prop:
                    name, type_hint = self._parse_prop_definition(prop)
                    props.append(FramerProperty(
                        name=name,
                        type=type_hint,
                        controls=self._suggest_control_type(name, type_hint),
                    ))

        # Look for state variables (useState)
        useState_pattern = r"const\s+\[(\w+),\s*set\w+\]\s*=\s*useState\s*\(([^)]*)\)"
        useState_matches = re.findall(useState_pattern, jsx_code)
        for var_name, initial_value in useState_matches:
            props.append(FramerProperty(
                name=var_name,
                type=self._infer_type_from_value(initial_value),
                default_value=initial_value,
                description=f"State variable: {var_name}",
                controls="input",
            ))

        return props

    def _parse_prop_definition(self, prop_def: str) -> Tuple[str, str]:
        """Parse a single prop definition."""
        # Handle TypeScript: "name: type"
        if ":" in prop_def:
            name, type_str = prop_def.split(":", 1)
            return name.strip(), type_str.strip()
        return prop_def.strip(), "any"

    def _infer_type_from_value(self, value: str) -> str:
        """Infer type from initial value."""
        value = value.strip()
        if value.startswith('"') or value.startswith("'"):
            return "string"
        elif value == "true" or value == "false":
            return "boolean"
        elif value.isdigit() or ("." in value and all(c.isdigit() or c == "." for c in value)):
            return "number"
        elif value.startswith("["):
            return "array"
        elif value.startswith("{"):
            return "object"
        return "any"

    def _suggest_control_type(self, prop_name: str, prop_type: str) -> str:
        """Suggest Framer control type for a prop."""
        name_lower = prop_name.lower()
        type_lower = prop_type.lower()

        if "color" in name_lower:
            return "colorControl"
        elif "toggle" in name_lower or prop_type == "boolean":
            return "toggle"
        elif "size" in name_lower or "width" in name_lower or "height" in name_lower:
            return "number"
        elif "disabled" in name_lower or "active" in name_lower:
            return "toggle"
        elif "text" in name_lower or "label" in name_lower or "placeholder" in name_lower:
            return "input"
        else:
            return "input"

    # ============ INTERACTIVE ELEMENTS ============

    def _find_interactive_elements(self, jsx_code: str) -> Dict[str, List[str]]:
        """Find interactive elements (buttons, inputs, etc.)."""
        interactive = {
            "buttons": [],
            "inputs": [],
            "forms": [],
            "event_handlers": [],
        }

        # Find buttons
        button_pattern = r"<button[^>]*>([^<]*)</button>"
        buttons = re.findall(button_pattern, jsx_code)
        interactive["buttons"] = buttons

        # Find inputs
        input_pattern = r"<input[^>]*type=['\"](\w+)['\"][^>]*>"
        inputs = re.findall(input_pattern, jsx_code)
        interactive["inputs"] = inputs

        # Find forms
        form_pattern = r"<form[^>]*>"
        forms = re.findall(form_pattern, jsx_code)
        interactive["forms"] = [str(f) for f in forms]

        # Find event handlers
        event_pattern = r"on\w+\s*=\s*\{[^}]*\}"
        events = re.findall(event_pattern, jsx_code)
        interactive["event_handlers"] = events

        return interactive

    def _add_framer_events(self, jsx_code: str, interactive_elements: Dict[str, List[str]]) -> str:
        """
        Add Framer-specific event handlers and animation hooks.
        
        Args:
            jsx_code: Original JSX code
            interactive_elements: Dict of interactive elements
            
        Returns:
            Enhanced JSX with Framer events
        """
        enhanced = jsx_code

        # Add motion to buttons
        if interactive_elements.get("buttons"):
            enhanced = enhanced.replace(
                "<button",
                '<button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}'
            )

        # Add animation support to inputs
        if interactive_elements.get("inputs"):
            enhanced = enhanced.replace(
                "<input",
                '<input animate={{ opacity: 1 }} initial={{ opacity: 0 }}'
            )

        # Ensure framer-motion is imported
        if "framer-motion" not in enhanced and "motion" in enhanced:
            enhanced = "import { motion } from 'framer-motion';\n" + enhanced

        return enhanced

    # ============ FRAMER CODE GENERATION ============

    def _generate_framer_wrapper(
        self,
        component_name: str,
        jsx_code: str,
        props: List[FramerProperty],
    ) -> str:
        """
        Generate Framer-compatible wrapper code.
        
        Args:
            component_name: Name of the component
            jsx_code: Enhanced JSX code
            props: List of props
            
        Returns:
            Complete Framer component code
        """
        # Generate prop definitions with Framer controls
        prop_definitions = self._generate_prop_definitions(props)

        # Generate exports
        wrapper_code = f'''
import {{ ComponentEntry, addComponentNotice }} from 'framer'
{self._generate_imports_from_jsx(jsx_code)}

/**
 * {component_name}
 * 
 * This component was auto-generated from orchestrator artifacts
 * and optimized for Framer Canvas.
 * 
 * @component
 */
export const {component_name} = {{
    description: "{component_name} - Generated Component",
    target: ({self._generate_component_call(component_name, props)}),
    props: {{
{prop_definitions}
    }},
    example: {{
{self._generate_example_props(props)}
    }},
}}

// Inline component definition
function {component_name}(props) {{
{self._indent_code(jsx_code, 4)}
}}

// Add Framer notice
addComponentNotice({{
    title: "{component_name}",
    description: "Interactive component generated from Langflow orchestrator",
}})

export default {component_name}
'''
        return wrapper_code.strip()

    def _generate_prop_definitions(self, props: List[FramerProperty]) -> str:
        """Generate Framer prop definitions."""
        if not props:
            return "        // No props defined"

        prop_lines = []
        for prop in props:
            prop_lines.append(f'''        {prop.name}: {{
            type: "{prop.type}",
            title: "{prop.name.replace('_', ' ').title()}",
            description: "{prop.description}",
            control: "{prop.controls}",
            {f'defaultValue: {self._format_value(prop.default_value)},' if prop.default_value else ''}
        }},''')

        return "\n".join(prop_lines)

    def _generate_component_call(self, component_name: str, props: List[FramerProperty]) -> str:
        """Generate component call signature."""
        if not props:
            return f"{component_name})"

        prop_names = ", ".join([f"{p.name}" for p in props])
        return f"{component_name} = ({{ {prop_names} }}) => {{"

    def _generate_example_props(self, props: List[FramerProperty]) -> str:
        """Generate example prop values."""
        if not props:
            return "        {}"

        example_lines = []
        for prop in props:
            example_lines.append(
                f"        {prop.name}: {self._format_example_value(prop)}"
            )

        return ",\n".join(example_lines)

    def _generate_imports_from_jsx(self, jsx_code: str) -> str:
        """Extract and format imports from JSX."""
        imports = self._extract_imports(jsx_code)
        if imports:
            return "\n".join(imports)
        return "import React, { useState } from 'react'"

    def _format_value(self, value: Any) -> str:
        """Format a value for Framer code."""
        if isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            return str(value)
        elif isinstance(value, dict):
            return str(value)
        return str(value)

    def _format_example_value(self, prop: FramerProperty) -> str:
        """Format example value based on prop type."""
        if prop.default_value:
            return self._format_value(prop.default_value)

        if prop.type == "string":
            return f"'{prop.name}'"
        elif prop.type == "boolean":
            return "true"
        elif prop.type == "number":
            return "0"
        elif prop.type == "array":
            return "[]"
        elif prop.type == "object":
            return "{}"
        return "null"

    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code by specified number of spaces."""
        indent = " " * spaces
        return "\n".join([f"{indent}{line}" for line in code.split("\n")])

    # ============ CANVAS CONFIGURATION ============

    def _generate_canvas_config(
        self,
        component_name: str,
        props: List[FramerProperty],
        project_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate canvas-specific configuration.
        
        Args:
            component_name: Component name
            props: List of props
            project_metadata: Project metadata
            
        Returns:
            Canvas configuration dict
        """
        return {
            "component_name": component_name,
            "canvas": {
                "width": project_metadata.get("canvas_width", 1200),
                "height": project_metadata.get("canvas_height", 800),
                "background": project_metadata.get("canvas_background", "#ffffff"),
                "grid": {
                    "enabled": True,
                    "size": 10,
                    "opacity": 0.1,
                },
            },
            "preview": {
                "enabled": True,
                "width": "100%",
                "height": "100%",
            },
            "props": {
                "editable": [p.name for p in props],
                "defaults": {
                    p.name: self._format_example_value(p) for p in props
                },
            },
        }

    # ============ ANIMATIONS CONFIGURATION ============

    def _generate_animations_config(self, interactive_elements: Dict[str, List[str]]) -> Dict[str, Any]:
        """Generate animations configuration for interactive elements."""
        return {
            "buttons": {
                "hover": {
                    "scale": 1.05,
                    "transition": {"duration": 0.2 },
                },
                "tap": {
                    "scale": 0.95,
                    "transition": {"duration": 0.1 },
                },
            },
            "inputs": {
                "focus": {
                    "borderColor": "#4f46e5",
                    "boxShadow": "0 0 0 3px rgba(79, 70, 229, 0.1)",
                    "transition": {"duration": 0.2 },
                },
                "hover": {
                    "borderColor": "#e5e7eb",
                },
            },
            "interactive": {
                "enabled": len(interactive_elements.get("event_handlers", [])) > 0,
                "event_count": len(interactive_elements.get("event_handlers", [])),
            },
        }

    # ============ SECONDARY ARTIFACTS ============

    def _generate_secondary_artifacts(
        self,
        component_name: str,
        jsx_code: str,
    ) -> List[Dict[str, Any]]:
        """
        Generate secondary artifacts (CSS modules, hooks, etc.).
        
        Args:
            component_name: Component name
            jsx_code: JSX code
            
        Returns:
            List of secondary artifacts
        """
        artifacts = []

        # Extract CSS if any
        css_blocks = re.findall(r"```css(.*?)```", jsx_code, re.DOTALL)
        for i, css in enumerate(css_blocks):
            artifacts.append({
                "type": "css",
                "name": f"{component_name}_styles_{i}.module.css",
                "content": css.strip(),
                "framer_compatible": True,
            })

        # Generate CSS modules from inline styles
        inline_styles = self._extract_inline_styles(jsx_code)
        if inline_styles:
            artifacts.append({
                "type": "css_module",
                "name": f"{component_name}.module.css",
                "content": inline_styles,
                "framer_compatible": True,
            })

        # Generate type definitions if TypeScript
        if "tsx" in jsx_code.lower() or ":" in jsx_code:
            ts_defs = self._generate_typescript_defs(component_name, jsx_code)
            artifacts.append({
                "type": "typescript",
                "name": f"{component_name}.types.ts",
                "content": ts_defs,
                "framer_compatible": True,
            })

        return artifacts

    def _extract_inline_styles(self, jsx_code: str) -> str:
        """Extract inline styles and convert to CSS module."""
        style_pattern = r"style\s*=\s*\{\{([^}]+)\}\}"
        styles = re.findall(style_pattern, jsx_code)

        if not styles:
            return ""

        css_content = ["/* Auto-generated CSS Module */\n", ".component {"]

        for style_group in styles:
            props = style_group.split(",")
            for prop in props:
                prop = prop.strip()
                if ":" in prop:
                    key, value = prop.split(":", 1)
                    css_key = self._camel_to_kebab(key.strip())
                    css_value = value.strip().replace("'", "").replace('"', "")
                    css_content.append(f"  {css_key}: {css_value};")

        css_content.append("}")

        return "\n".join(css_content)

    def _camel_to_kebab(self, name: str) -> str:
        """Convert camelCase to kebab-case."""
        return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()

    def _generate_typescript_defs(self, component_name: str, jsx_code: str) -> str:
        """Generate TypeScript type definitions."""
        props = self._extract_props(jsx_code)

        type_defs = f"""/**
 * {component_name} Component Types
 * Auto-generated from Langflow orchestrator
 */

export interface {component_name}Props {{
"""

        for prop in props:
            ts_type = self._python_to_ts_type(prop.type)
            type_defs += f"  {prop.name}?: {ts_type}; // {prop.description}\n"

        type_defs += f"""}}

export interface {component_name}State {{
  [key: string]: any;
}}

export type {component_name}Component = React.FC<{component_name}Props>;
"""

        return type_defs

    def _python_to_ts_type(self, py_type: str) -> str:
        """Convert Python type hint to TypeScript type."""
        type_map = {
            "string": "string",
            "number": "number",
            "boolean": "boolean",
            "array": "any[]",
            "object": "Record<string, any>",
            "any": "any",
        }
        return type_map.get(py_type.lower(), "any")

    # ============ STORAGE ============

    def save_framer_component(
        self,
        run_id: UUID,
        project_id: UUID,
        result: FramerExportResult,
    ) -> None:
        """
        Save Framer component to database.
        
        Args:
            run_id: Orchestration run ID
            project_id: Project ID
            result: FramerExportResult
        """
        try:
            # Save main Framer component
            artifact = GeneratedArtifact(
                run_id=run_id,
                project_id=project_id,
                artifact_type="framer_component",
                name=f"{result.component_name}.framer.tsx",
                content=result.framer_code,
                metadata={
                    "canvas_config": result.canvas_config,
                    "animations_config": result.animations_config,
                    "generation_time": result.generation_time,
                },
            )
            self.session.add(artifact)

            # Save secondary artifacts
            for secondary in result.artifacts:
                secondary_artifact = GeneratedArtifact(
                    run_id=run_id,
                    project_id=project_id,
                    artifact_type=secondary.get("type", "supporting"),
                    name=secondary.get("name", "artifact"),
                    content=secondary.get("content", ""),
                    metadata={"framer_compatible": True},
                )
                self.session.add(secondary_artifact)

            self.session.commit()

        except Exception as e:
            self.session.rollback()
            raise Exception(f"Failed to save Framer component: {str(e)}")
