"""Gemini 2.5 Pro Integration Service.

Integrates Google's Gemini 2.5 Pro API for prompt optimization, code enhancement,
and quality improvement of generated components and code.

This service acts as an enhancement layer that can be optionally applied to
improve output from the Orchestrator and Framer Generator.
"""

import os
import json
import re
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, Any, Dict, List, Tuple
from enum import Enum
from dataclasses import dataclass, field

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiModel(str, Enum):
    """Available Gemini models."""
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_1_5_PRO = "gemini-1.5-pro"


class EnhancementType(str, Enum):
    """Types of enhancements available."""
    PROMPT_CLEAN = "prompt_clean"
    CODE_QUALITY = "code_quality"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"


@dataclass
class GeminiPrompt:
    """Prompt configuration for Gemini."""
    content: str
    system_instruction: str = ""
    model: GeminiModel = GeminiModel.GEMINI_2_5_PRO
    temperature: float = 0.7
    top_p: float = 0.95
    max_tokens: int = 2048


@dataclass
class GeminiResponse:
    """Response from Gemini API."""
    content: str
    finish_reason: str
    usage_input_tokens: int = 0
    usage_output_tokens: int = 0
    generation_time: float = 0.0


@dataclass
class EnhancementResult:
    """Result of an enhancement operation."""
    run_id: Optional[UUID] = None
    enhancement_type: EnhancementType = EnhancementType.PROMPT_CLEAN
    original_content: str = ""
    enhanced_content: str = ""
    suggestions: List[str] = field(default_factory=list)
    quality_score_before: float = 0.0
    quality_score_after: float = 0.0
    generation_time: float = 0.0
    status: str = "SUCCESS"
    error: Optional[str] = None


class GeminiIntegration:
    """Integration service for Gemini 2.5 Pro API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini integration.
        
        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai library not installed. "
                "Install with: pip install google-generativeai"
            )

        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable not set and no API key provided"
            )

        genai.configure(api_key=self.api_key)
        self.client = genai
        self.model = GeminiModel.GEMINI_2_5_PRO

    # ============ PROMPT ENHANCEMENT ============

    def clean_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> EnhancementResult:
        """
        Clean and optimize a prompt for better model generation.
        
        Args:
            prompt: Original prompt text
            context: Optional context about the generation
            
        Returns:
            EnhancementResult with cleaned prompt
        """
        start_time = datetime.now(timezone.utc)

        try:
            system_instruction = """You are a prompt optimization expert. Your task is to:
1. Clean up the prompt for clarity and precision
2. Remove redundancy and ambiguity
3. Add specific instructions where needed
4. Ensure technical accuracy
5. Make it concise but complete

Return ONLY the improved prompt, no explanations."""

            response = self._call_gemini(
                content=prompt,
                system_instruction=system_instruction,
                max_tokens=1024,
            )

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

            return EnhancementResult(
                enhancement_type=EnhancementType.PROMPT_CLEAN,
                original_content=prompt,
                enhanced_content=response.content.strip(),
                generation_time=elapsed,
                quality_score_before=self._calculate_prompt_quality(prompt),
                quality_score_after=self._calculate_prompt_quality(response.content),
                status="SUCCESS",
            )

        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            return EnhancementResult(
                enhancement_type=EnhancementType.PROMPT_CLEAN,
                original_content=prompt,
                status="FAILED",
                error=str(e),
                generation_time=elapsed,
            )

    # ============ CODE ENHANCEMENT ============

    def enhance_code_quality(self, code: str, language: str = "javascript") -> EnhancementResult:
        """
        Enhance code quality by suggesting improvements.
        
        Args:
            code: Source code to enhance
            language: Programming language (javascript, typescript, python, etc)
            
        Returns:
            EnhancementResult with quality improvements
        """
        start_time = datetime.now(timezone.utc)

        try:
            system_instruction = f"""You are a {language} code quality expert. Analyze the code and:
1. Identify potential improvements
2. Suggest better practices
3. Optimize performance where applicable
4. Add missing error handling
5. Improve readability

Return the improved code maintaining the same functionality."""

            response = self._call_gemini(
                content=f"```{language}\n{code}\n```",
                system_instruction=system_instruction,
                max_tokens=2048,
            )

            # Extract code from response
            enhanced_code = self._extract_code_from_response(response.content, language)

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

            return EnhancementResult(
                enhancement_type=EnhancementType.CODE_QUALITY,
                original_content=code,
                enhanced_content=enhanced_code,
                generation_time=elapsed,
                quality_score_before=self._calculate_code_quality(code, language),
                quality_score_after=self._calculate_code_quality(enhanced_code, language),
                status="SUCCESS",
            )

        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            return EnhancementResult(
                enhancement_type=EnhancementType.CODE_QUALITY,
                original_content=code,
                status="FAILED",
                error=str(e),
                generation_time=elapsed,
            )

    def enhance_accessibility(self, jsx_code: str) -> EnhancementResult:
        """
        Enhance JSX/TSX component for accessibility.
        
        Args:
            jsx_code: React component code
            
        Returns:
            EnhancementResult with accessibility improvements
        """
        start_time = datetime.now(timezone.utc)

        try:
            system_instruction = """You are a web accessibility expert. Enhance this React component for:
1. ARIA labels and roles
2. Keyboard navigation
3. Focus management
4. Screen reader support
5. Color contrast
6. Semantic HTML

Return only the improved component code."""

            response = self._call_gemini(
                content=f"```jsx\n{jsx_code}\n```",
                system_instruction=system_instruction,
                max_tokens=2048,
            )

            enhanced_code = self._extract_code_from_response(response.content, "jsx")

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

            return EnhancementResult(
                enhancement_type=EnhancementType.ACCESSIBILITY,
                original_content=jsx_code,
                enhanced_content=enhanced_code,
                generation_time=elapsed,
                suggestions=self._extract_suggestions(response.content),
                status="SUCCESS",
            )

        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            return EnhancementResult(
                enhancement_type=EnhancementType.ACCESSIBILITY,
                original_content=jsx_code,
                status="FAILED",
                error=str(e),
                generation_time=elapsed,
            )

    def enhance_performance(self, code: str, language: str = "javascript") -> EnhancementResult:
        """
        Enhance code for performance.
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            EnhancementResult with performance optimizations
        """
        start_time = datetime.now(timezone.utc)

        try:
            system_instruction = f"""You are a {language} performance expert. Optimize this code for:
1. Runtime efficiency
2. Memory usage
3. Algorithm complexity
4. Caching opportunities
5. Lazy loading
6. Tree shaking (if applicable)

Return the optimized code with the same functionality."""

            response = self._call_gemini(
                content=f"```{language}\n{code}\n```",
                system_instruction=system_instruction,
                max_tokens=2048,
            )

            enhanced_code = self._extract_code_from_response(response.content, language)

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

            return EnhancementResult(
                enhancement_type=EnhancementType.PERFORMANCE,
                original_content=code,
                enhanced_content=enhanced_code,
                generation_time=elapsed,
                suggestions=self._extract_suggestions(response.content),
                status="SUCCESS",
            )

        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            return EnhancementResult(
                enhancement_type=EnhancementType.PERFORMANCE,
                original_content=code,
                status="FAILED",
                error=str(e),
                generation_time=elapsed,
            )

    def enhance_security(self, code: str, language: str = "javascript") -> EnhancementResult:
        """
        Enhance code for security vulnerabilities.
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            EnhancementResult with security improvements
        """
        start_time = datetime.now(timezone.utc)

        try:
            system_instruction = f"""You are a security expert. Review and enhance this {language} code for:
1. SQL injection prevention
2. XSS protection
3. CSRF tokens
4. Input validation
5. Authentication/authorization
6. Secure data handling
7. Environment variables for secrets

Return the secure version of the code."""

            response = self._call_gemini(
                content=f"```{language}\n{code}\n```",
                system_instruction=system_instruction,
                max_tokens=2048,
            )

            enhanced_code = self._extract_code_from_response(response.content, language)

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

            return EnhancementResult(
                enhancement_type=EnhancementType.SECURITY,
                original_content=code,
                enhanced_content=enhanced_code,
                generation_time=elapsed,
                suggestions=self._extract_suggestions(response.content),
                status="SUCCESS",
            )

        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            return EnhancementResult(
                enhancement_type=EnhancementType.SECURITY,
                original_content=code,
                status="FAILED",
                error=str(e),
                generation_time=elapsed,
            )

    def add_documentation(self, code: str, language: str = "javascript") -> EnhancementResult:
        """
        Add comprehensive documentation to code.
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            EnhancementResult with added documentation
        """
        start_time = datetime.now(timezone.utc)

        try:
            system_instruction = f"""You are a documentation expert for {language}. Add comprehensive documentation to:
1. Functions/methods with JSDoc/docstrings
2. Parameters and return types
3. Complex logic with comments
4. Edge cases
5. Usage examples where helpful

Return the fully documented code."""

            response = self._call_gemini(
                content=f"```{language}\n{code}\n```",
                system_instruction=system_instruction,
                max_tokens=2048,
            )

            enhanced_code = self._extract_code_from_response(response.content, language)

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

            return EnhancementResult(
                enhancement_type=EnhancementType.DOCUMENTATION,
                original_content=code,
                enhanced_content=enhanced_code,
                generation_time=elapsed,
                status="SUCCESS",
            )

        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            return EnhancementResult(
                enhancement_type=EnhancementType.DOCUMENTATION,
                original_content=code,
                status="FAILED",
                error=str(e),
                generation_time=elapsed,
            )

    # ============ BATCH ENHANCEMENT ============

    def batch_enhance(
        self,
        items: List[Dict[str, Any]],
        enhancement_type: EnhancementType = EnhancementType.PROMPT_CLEAN,
    ) -> List[EnhancementResult]:
        """
        Apply enhancement to multiple items in batch.
        
        Args:
            items: List of items to enhance
            enhancement_type: Type of enhancement
            
        Returns:
            List of EnhancementResult objects
        """
        results = []

        for item in items:
            content = item.get("content", "")

            if enhancement_type == EnhancementType.PROMPT_CLEAN:
                result = self.clean_prompt(content, item.get("context"))
            elif enhancement_type == EnhancementType.CODE_QUALITY:
                result = self.enhance_code_quality(content, item.get("language", "javascript"))
            elif enhancement_type == EnhancementType.ACCESSIBILITY:
                result = self.enhance_accessibility(content)
            elif enhancement_type == EnhancementType.PERFORMANCE:
                result = self.enhance_performance(content, item.get("language", "javascript"))
            elif enhancement_type == EnhancementType.SECURITY:
                result = self.enhance_security(content, item.get("language", "javascript"))
            elif enhancement_type == EnhancementType.DOCUMENTATION:
                result = self.add_documentation(content, item.get("language", "javascript"))
            else:
                result = EnhancementResult(status="UNSUPPORTED", error="Enhancement type not supported")

            results.append(result)

        return results

    # ============ INTERNAL HELPERS ============

    def _call_gemini(
        self,
        content: str,
        system_instruction: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> GeminiResponse:
        """
        Call Gemini API with given parameters.
        
        Args:
            content: Prompt content
            system_instruction: System-level instruction
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            GeminiResponse with API response
        """
        try:
            model = genai.GenerativeModel(
                model_name=self.model.value,
                system_instruction=system_instruction if system_instruction else None,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )

            response = model.generate_content(content)

            return GeminiResponse(
                content=response.text,
                finish_reason=response.candidates[0].finish_reason if response.candidates else "UNKNOWN",
                usage_input_tokens=response.usage_metadata.input_tokens if response.usage_metadata else 0,
                usage_output_tokens=response.usage_metadata.output_tokens if response.usage_metadata else 0,
            )

        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

    def _extract_code_from_response(self, response: str, language: str) -> str:
        """
        Extract code from Gemini response (handles markdown code blocks).
        
        Args:
            response: Response text from Gemini
            language: Programming language
            
        Returns:
            Extracted code
        """
        # Try to extract from code block
        pattern = rf"```{language}\n(.*?)\n```"
        match = re.search(pattern, response, re.DOTALL)

        if match:
            return match.group(1).strip()

        # Try generic code block
        pattern = r"```\n(.*?)\n```"
        match = re.search(pattern, response, re.DOTALL)

        if match:
            return match.group(1).strip()

        # Return as-is if no code block found
        return response.strip()

    def _extract_suggestions(self, response: str) -> List[str]:
        """Extract suggestions/improvements from response."""
        suggestions = []

        # Look for bullet points
        bullet_pattern = r"[•\-\*]\s+(.+)"
        matches = re.findall(bullet_pattern, response)
        suggestions.extend(matches)

        # Look for numbered items
        num_pattern = r"\d+\.\s+(.+)"
        matches = re.findall(num_pattern, response)
        suggestions.extend(matches)

        return suggestions[:10]  # Limit to 10 suggestions

    def _calculate_prompt_quality(self, prompt: str) -> float:
        """
        Simple heuristic to calculate prompt quality (0-1).
        
        Args:
            prompt: Prompt text
            
        Returns:
            Quality score 0-1
        """
        score = 0.0

        # Length factor (too short or too long is bad)
        length = len(prompt.split())
        if 10 <= length <= 200:
            score += 0.3
        elif 5 <= length < 250:
            score += 0.2

        # Clarity factors
        if "?" not in prompt and "!" in prompt:
            score += 0.2

        if any(word in prompt.lower() for word in ["code", "generate", "create", "build"]):
            score += 0.2

        # Specificity
        if any(word in prompt.lower() for word in ["specific", "detail", "example", "exact"]):
            score += 0.2

        return min(score, 1.0)

    def _calculate_code_quality(self, code: str, language: str = "javascript") -> float:
        """
        Simple heuristic to calculate code quality (0-1).
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            Quality score 0-1
        """
        score = 0.0

        # Length factor
        lines = len(code.split("\n"))
        if lines > 5:
            score += 0.2

        # Has documentation
        if "//" in code or "/*" in code or '"""' in code or "'''" in code:
            score += 0.2

        # Has error handling
        if "try" in code or "catch" in code or "except" in code or "finally" in code:
            score += 0.2

        # Has type hints/annotations
        if ":" in code and language == "python":
            score += 0.2
        elif ":" in code and language in ["typescript", "javascript"]:
            score += 0.1

        # Has functions/methods
        if "def " in code or "function" in code or "const " in code:
            score += 0.2

        return min(score, 1.0)

    # ============ AVAILABILITY CHECK ============

    @staticmethod
    def is_available() -> bool:
        """Check if Gemini integration is available."""
        return GEMINI_AVAILABLE and bool(os.getenv("GOOGLE_API_KEY"))

    @staticmethod
    def check_api_key() -> Tuple[bool, str]:
        """
        Check if API key is properly configured.
        
        Returns:
            (is_configured, message)
        """
        api_key = os.getenv("GOOGLE_API_KEY")

        if not GEMINI_AVAILABLE:
            return False, "google-generativeai library not installed"

        if not api_key:
            return False, "GOOGLE_API_KEY environment variable not set"

        if len(api_key) < 20:
            return False, "API key appears to be invalid (too short)"

        return True, "API key is properly configured"
