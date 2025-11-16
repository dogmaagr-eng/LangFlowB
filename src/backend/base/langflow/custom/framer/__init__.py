"""Framer Component Generator Package.

This package provides services for converting Langflow orchestrator artifacts
(JSX/TSX components) into Framer-compatible interactive components with full
canvas support, property binding, and animation configuration.

Main Components:
    - FramerComponentGenerator: Core service for component conversion
    - FramerComponent: Data class for component definitions
    - FramerExportResult: Result wrapper for generation operations
    - API Routes: FastAPI endpoints for component generation and management

Features:
    - Automatic JSX/TSX to Framer conversion
    - Interactive element detection and event binding
    - Property extraction and Framer control generation
    - Canvas configuration generation
    - Animation setup for interactive elements
    - Multi-format export (TSX, JSON, HTML)
    - Batch operation support
    - Database persistence

Usage:
    >>> from src.backend.base.langflow.custom.framer.service import FramerComponentGenerator
    >>> generator = FramerComponentGenerator(session)
    >>> results = generator.convert_artifacts_to_framer(
    ...     run_id=uuid,
    ...     artifacts=[{"type": "jsx", "name": "Button.jsx", "content": "..."}]
    ... )
"""

from .service import (
    FramerComponentGenerator,
    FramerComponent,
    FramerExportResult,
    FramerProperty,
    ComponentType,
    AnimationType,
)
from .routes import router

__all__ = [
    "FramerComponentGenerator",
    "FramerComponent",
    "FramerExportResult",
    "FramerProperty",
    "ComponentType",
    "AnimationType",
    "router",
]

__version__ = "1.0.0"
__author__ = "Langflow"
__description__ = "Framer Component Generator - Convert orchestrator artifacts to interactive Framer components"
