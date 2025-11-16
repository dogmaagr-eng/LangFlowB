"""Gemini 2.5 Pro Integration Package.

This package provides integration with Google's Gemini 2.5 Pro API for enhancing
generated components and code with advanced AI capabilities.

Main Components:
    - GeminiIntegration: Core service for API interaction
    - EnhancementType: Enum of available enhancement types
    - EnhancementResult: Result wrapper for enhancement operations
    - API Routes: FastAPI endpoints for enhancement services

Features:
    - Prompt cleaning and optimization
    - Code quality enhancement
    - Accessibility improvements (WCAG compliance)
    - Performance optimization
    - Security vulnerability detection
    - Documentation generation
    - Batch operation support
    - Multiple model support

Usage:
    >>> from src.backend.base.langflow.custom.gemini.service import GeminiIntegration
    >>> integration = GeminiIntegration(api_key="your-api-key")
    >>> result = integration.clean_prompt("Generate a React button component")
    >>> print(result.enhanced_content)
"""

from .service import (
    GeminiIntegration,
    GeminiModel,
    GeminiResponse,
    EnhancementType,
    EnhancementResult,
    GeminiPrompt,
    GEMINI_AVAILABLE,
)
from .routes import router

__all__ = [
    "GeminiIntegration",
    "GeminiModel",
    "GeminiResponse",
    "EnhancementType",
    "EnhancementResult",
    "GeminiPrompt",
    "GEMINI_AVAILABLE",
    "router",
]

__version__ = "1.0.0"
__author__ = "Langflow"
__description__ = "Gemini 2.5 Pro Integration - Enhance components and code with AI"
