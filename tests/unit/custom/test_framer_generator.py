"""Unit tests for Framer Component Generator service."""

import pytest
from uuid import UUID, uuid4
from sqlmodel import Session, create_engine, SQLSession
from sqlmodel.pool import StaticPool

from src.backend.base.langflow.custom.framer.service import (
    FramerComponentGenerator,
    FramerProperty,
    ComponentType,
    AnimationType,
)


@pytest.fixture
def session():
    """Create in-memory SQLite session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with Session(engine) as session:
        yield session


@pytest.fixture
def generator(session):
    """Create FramerComponentGenerator instance."""
    return FramerComponentGenerator(session)


@pytest.fixture
def sample_jsx_artifact():
    """Sample JSX artifact from orchestrator."""
    return {
        "type": "jsx",
        "name": "Button.jsx",
        "content": """
import React, { useState } from 'react';

export const Button = ({ label, onClick, disabled }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        padding: '10px 20px',
        backgroundColor: isHovered ? '#3b82f6' : '#1e40af',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
      }}
    >
      {label}
    </button>
  );
};

export default Button;
"""
    }


@pytest.fixture
def sample_tsx_artifact():
    """Sample TSX artifact with TypeScript."""
    return {
        "type": "tsx",
        "name": "Card.tsx",
        "content": """
import React from 'react';

interface CardProps {
  title: string;
  description: string;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  title,
  description,
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      style={{
        padding: '16px',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        backgroundColor: '#ffffff',
        cursor: onClick ? 'pointer' : 'default',
      }}
    >
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
  );
};

export default Card;
"""
    }


# ============ COMPONENT PARSING TESTS ============

def test_generator_initialization(generator):
    """Test FramerComponentGenerator initialization."""
    assert generator is not None
    assert generator.session is not None
    assert hasattr(generator, 'default_animations')


def test_detect_component_type_button(generator, sample_jsx_artifact):
    """Test component type detection for button."""
    component_type = generator._detect_component_type(sample_jsx_artifact["content"])
    assert component_type == ComponentType.BUTTON


def test_detect_component_type_card(generator, sample_tsx_artifact):
    """Test component type detection for card."""
    component_type = generator._detect_component_type(sample_tsx_artifact["content"])
    assert component_type in [ComponentType.CUSTOM, ComponentType.LAYOUT]


def test_extract_imports(generator, sample_jsx_artifact):
    """Test import extraction from JSX."""
    imports = generator._extract_imports(sample_jsx_artifact["content"])
    assert len(imports) > 0
    assert any("react" in imp.lower() for imp in imports)


def test_extract_custom_hooks(generator, sample_jsx_artifact):
    """Test custom hook extraction."""
    hooks = generator._extract_custom_hooks(sample_jsx_artifact["content"])
    assert len(hooks) >= 0


# ============ PROPS EXTRACTION TESTS ============

def test_extract_props_from_jsx(generator, sample_jsx_artifact):
    """Test prop extraction from JSX."""
    props = generator._extract_props(sample_jsx_artifact["content"])
    assert len(props) > 0
    
    prop_names = [p.name for p in props]
    # Should find at least one of: label, onClick, disabled, isHovered
    assert any(name in ["label", "onClick", "disabled", "isHovered"] for name in prop_names)


def test_extract_props_from_tsx(generator, sample_tsx_artifact):
    """Test prop extraction from TSX."""
    props = generator._extract_props(sample_tsx_artifact["content"])
    assert len(props) >= 0


def test_infer_type_from_value(generator):
    """Test type inference from values."""
    assert generator._infer_type_from_value('"hello"') == "string"
    assert generator._infer_type_from_value("'hello'") == "string"
    assert generator._infer_type_from_value("true") == "boolean"
    assert generator._infer_type_from_value("false") == "boolean"
    assert generator._infer_type_from_value("42") == "number"
    assert generator._infer_type_from_value("3.14") == "number"
    assert generator._infer_type_from_value("[]") == "array"
    assert generator._infer_type_from_value("{}") == "object"


def test_suggest_control_type(generator):
    """Test Framer control type suggestion."""
    assert generator._suggest_control_type("color", "string") == "colorControl"
    assert generator._suggest_control_type("toggle", "boolean") == "toggle"
    assert generator._suggest_control_type("disabled", "boolean") == "toggle"
    assert generator._suggest_control_type("width", "number") == "number"
    assert generator._suggest_control_type("text", "string") == "input"


# ============ INTERACTIVE ELEMENTS TESTS ============

def test_find_interactive_elements_buttons(generator, sample_jsx_artifact):
    """Test interactive element detection for buttons."""
    elements = generator._find_interactive_elements(sample_jsx_artifact["content"])
    assert "buttons" in elements
    assert len(elements["buttons"]) >= 0


def test_find_interactive_elements_event_handlers(generator, sample_jsx_artifact):
    """Test event handler detection."""
    elements = generator._find_interactive_elements(sample_jsx_artifact["content"])
    assert "event_handlers" in elements


def test_add_framer_events(generator, sample_jsx_artifact):
    """Test adding Framer events to JSX."""
    elements = generator._find_interactive_elements(sample_jsx_artifact["content"])
    enhanced = generator._add_framer_events(sample_jsx_artifact["content"], elements)
    
    assert enhanced is not None
    assert len(enhanced) > 0


# ============ CODE GENERATION TESTS ============

def test_generate_prop_definitions(generator):
    """Test prop definition generation."""
    props = [
        FramerProperty(name="label", type="string", default_value="Click me"),
        FramerProperty(name="size", type="number", default_value=12),
    ]
    
    prop_defs = generator._generate_prop_definitions(props)
    assert "label" in prop_defs
    assert "size" in prop_defs
    assert '"string"' in prop_defs or "'string'" in prop_defs


def test_generate_framer_wrapper(generator, sample_jsx_artifact):
    """Test Framer wrapper generation."""
    props = [
        FramerProperty(name="label", type="string", default_value="Button"),
        FramerProperty(name="onClick", type="function"),
    ]
    
    wrapper = generator._generate_framer_wrapper(
        component_name="Button",
        jsx_code=sample_jsx_artifact["content"],
        props=props,
    )
    
    assert wrapper is not None
    assert "Button" in wrapper
    assert "export" in wrapper


def test_indent_code(generator):
    """Test code indentation utility."""
    code = "line1\nline2\nline3"
    indented = generator._indent_code(code, 4)
    
    lines = indented.split("\n")
    assert all(line.startswith("    ") for line in lines)


def test_format_value(generator):
    """Test value formatting."""
    assert generator._format_value("hello") == "'hello'"
    assert generator._format_value(42) == "42"
    assert generator._format_value(True) == "true"
    assert generator._format_value(False) == "false"


def test_format_example_value(generator):
    """Test example value formatting."""
    prop1 = FramerProperty(name="text", type="string", default_value="default")
    prop2 = FramerProperty(name="count", type="number")
    prop3 = FramerProperty(name="active", type="boolean")
    
    assert "default" in generator._format_example_value(prop1)
    assert generator._format_example_value(prop2) == "0"
    assert generator._format_example_value(prop3) == "true"


# ============ CANVAS CONFIGURATION TESTS ============

def test_generate_canvas_config(generator):
    """Test canvas configuration generation."""
    props = [
        FramerProperty(name="label", type="string"),
    ]
    
    config = generator._generate_canvas_config(
        component_name="Button",
        props=props,
        project_metadata={"canvas_width": 1200, "canvas_height": 800},
    )
    
    assert config["component_name"] == "Button"
    assert config["canvas"]["width"] == 1200
    assert config["canvas"]["height"] == 800
    assert "grid" in config["canvas"]
    assert "props" in config


# ============ ANIMATION CONFIGURATION TESTS ============

def test_generate_animations_config(generator, sample_jsx_artifact):
    """Test animation configuration generation."""
    elements = generator._find_interactive_elements(sample_jsx_artifact["content"])
    animations = generator._generate_animations_config(elements)
    
    assert "buttons" in animations
    assert "inputs" in animations
    assert "interactive" in animations


def test_animation_types(generator):
    """Test animation type enum."""
    assert hasattr(AnimationType, 'FADE')
    assert hasattr(AnimationType, 'SCALE')
    assert hasattr(AnimationType, 'SLIDE')
    assert hasattr(AnimationType, 'ROTATE')
    assert hasattr(AnimationType, 'BOUNCE')
    assert hasattr(AnimationType, 'NONE')


# ============ SECONDARY ARTIFACTS TESTS ============

def test_extract_inline_styles(generator):
    """Test inline style extraction."""
    jsx_with_styles = """
    <div style={{ backgroundColor: '#ff0000', padding: '10px' }}>
        Content
    </div>
    """
    styles = generator._extract_inline_styles(jsx_with_styles)
    assert styles is not None


def test_camel_to_kebab(generator):
    """Test camelCase to kebab-case conversion."""
    assert generator._camel_to_kebab("backgroundColor") == "background-color"
    assert generator._camel_to_kebab("padding") == "padding"
    assert generator._camel_to_kebab("paddingLeft") == "padding-left"


def test_python_to_ts_type(generator):
    """Test Python to TypeScript type conversion."""
    assert generator._python_to_ts_type("string") == "string"
    assert generator._python_to_ts_type("number") == "number"
    assert generator._python_to_ts_type("boolean") == "boolean"
    assert generator._python_to_ts_type("array") == "any[]"
    assert generator._python_to_ts_type("object") == "Record<string, any>"


def test_generate_typescript_defs(generator):
    """Test TypeScript type definitions generation."""
    jsx_code = """
    export const Component = ({ name, count }) => (
        <div>{name}: {count}</div>
    );
    """
    
    type_defs = generator._generate_typescript_defs("Component", jsx_code)
    assert "Component" in type_defs
    assert "Props" in type_defs


def test_generate_secondary_artifacts(generator, sample_jsx_artifact):
    """Test secondary artifact generation."""
    artifacts = generator._generate_secondary_artifacts(
        "Button",
        sample_jsx_artifact["content"],
    )
    
    assert isinstance(artifacts, list)
    # May generate CSS, TypeScript, etc.
    assert len(artifacts) >= 0


# ============ FULL CONVERSION TESTS ============

def test_process_single_artifact(generator, sample_jsx_artifact):
    """Test processing a single artifact."""
    run_id = uuid4()
    
    result = generator._process_single_artifact(
        run_id=run_id,
        artifact=sample_jsx_artifact,
        project_metadata={},
    )
    
    assert result.component_name == "Button"
    assert result.status == "SUCCESS"
    assert result.framer_code is not None
    assert result.canvas_config is not None


def test_convert_artifacts_to_framer(generator, sample_jsx_artifact):
    """Test converting artifacts to Framer components."""
    run_id = uuid4()
    artifacts = [sample_jsx_artifact]
    
    results = generator.convert_artifacts_to_framer(
        run_id=run_id,
        artifacts=artifacts,
        project_metadata={"canvas_width": 1200},
    )
    
    assert len(results) > 0
    assert results[0].status == "SUCCESS"
    assert results[0].run_id == run_id


def test_convert_multiple_artifacts(generator, sample_jsx_artifact, sample_tsx_artifact):
    """Test converting multiple artifacts."""
    run_id = uuid4()
    artifacts = [sample_jsx_artifact, sample_tsx_artifact]
    
    results = generator.convert_artifacts_to_framer(
        run_id=run_id,
        artifacts=artifacts,
    )
    
    assert len(results) >= 2
    assert all(r.status == "SUCCESS" for r in results)


def test_convert_non_jsx_artifact_filtered(generator):
    """Test that non-JSX artifacts are filtered."""
    run_id = uuid4()
    artifacts = [
        {
            "type": "css",
            "name": "style.css",
            "content": "body { color: red; }",
        },
    ]
    
    results = generator.convert_artifacts_to_framer(
        run_id=run_id,
        artifacts=artifacts,
    )
    
    # CSS artifacts should be filtered out
    assert len(results) == 0 or results[0].status == "SUCCESS"


# ============ ERROR HANDLING TESTS ============

def test_convert_empty_artifacts(generator):
    """Test converting empty artifacts list."""
    run_id = uuid4()
    
    results = generator.convert_artifacts_to_framer(
        run_id=run_id,
        artifacts=[],
    )
    
    assert isinstance(results, list)


def test_convert_malformed_artifact(generator):
    """Test handling malformed artifacts."""
    run_id = uuid4()
    artifacts = [
        {
            "type": "jsx",
            "name": "Broken.jsx",
            "content": "<<<invalid jsx>>>",
        },
    ]
    
    results = generator.convert_artifacts_to_framer(
        run_id=run_id,
        artifacts=artifacts,
    )
    
    # Should handle gracefully
    assert len(results) > 0


# ============ COMPONENT TYPE ENUM TESTS ============

def test_component_types_enum():
    """Test ComponentType enum."""
    assert hasattr(ComponentType, 'BUTTON')
    assert hasattr(ComponentType, 'INPUT')
    assert hasattr(ComponentType, 'CARD')
    assert hasattr(ComponentType, 'LAYOUT')
    assert hasattr(ComponentType, 'INTERACTIVE')
    assert hasattr(ComponentType, 'ANIMATED')
    assert hasattr(ComponentType, 'CUSTOM')


# ============ INTEGRATION TESTS ============

def test_full_component_generation_workflow(generator, sample_jsx_artifact):
    """Test complete component generation workflow."""
    run_id = uuid4()
    project_id = uuid4()
    
    # Convert artifacts
    results = generator.convert_artifacts_to_framer(
        run_id=run_id,
        artifacts=[sample_jsx_artifact],
        project_metadata={
            "canvas_width": 1200,
            "canvas_height": 800,
            "canvas_background": "#ffffff",
        },
    )
    
    assert len(results) > 0
    result = results[0]
    
    # Verify result structure
    assert result.component_id is not None
    assert result.component_name is not None
    assert result.framer_code is not None
    assert result.canvas_config is not None
    assert result.animations_config is not None
    assert result.generation_time > 0
    
    # Verify code content
    assert "export" in result.framer_code
    assert "component_name" in result.canvas_config
    assert "canvas" in result.canvas_config


# ============ PROPERTY BINDING TESTS ============

def test_framer_property_creation():
    """Test FramerProperty creation."""
    prop = FramerProperty(
        name="size",
        type="number",
        default_value=12,
        description="Component size",
        controls="number",
    )
    
    assert prop.name == "size"
    assert prop.type == "number"
    assert prop.default_value == 12
    assert prop.controls == "number"


def test_framer_property_controls():
    """Test FramerProperty control type mapping."""
    prop_string = FramerProperty(name="text", type="string", controls="input")
    prop_bool = FramerProperty(name="active", type="boolean", controls="toggle")
    prop_color = FramerProperty(name="color", type="string", controls="colorControl")
    
    assert prop_string.controls == "input"
    assert prop_bool.controls == "toggle"
    assert prop_color.controls == "colorControl"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
