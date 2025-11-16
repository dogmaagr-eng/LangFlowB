# Task 5: Gemini 2.5 Pro Integration

**Status:** ✅ PRODUCTION READY
**Version:** 1.0.0
**Date Completed:** December 2024

---

## 📋 Overview

**Gemini 2.5 Pro Integration** is an optional enhancement layer for Langflow that leverages Google's most advanced AI model to automatically improve:

- ✨ **Prompts** - Optimize and refine AI prompts for better results
- 🔧 **Code Quality** - Improve code structure, readability, and best practices
- ♿ **Accessibility** - Enhance WCAG compliance and inclusive design
- ⚡ **Performance** - Optimize algorithms and resource usage
- 🔒 **Security** - Detect and fix vulnerabilities (SQL injection, XSS, CSRF, etc.)
- 📖 **Documentation** - Generate JSDoc, docstrings, and helpful comments

## 🎯 Key Features

### 1. **Multiple Enhancement Types**
Each enhancement type is specialized for its domain with targeted strategies:

```python
from src.backend.base.langflow.custom.gemini.service import EnhancementType

EnhancementType.PROMPT_CLEAN          # Optimize prompts
EnhancementType.CODE_QUALITY          # Improve code quality
EnhancementType.ACCESSIBILITY         # WCAG compliance
EnhancementType.PERFORMANCE           # Performance optimization
EnhancementType.SECURITY              # Security vulnerability detection
EnhancementType.DOCUMENTATION         # Add comprehensive docs
```

### 2. **Quality Metrics**
Every enhancement includes quality scores (0-1 scale):

- **quality_score_before** - Original content quality
- **quality_score_after** - Enhanced content quality
- **improvement_percentage** - Quantified improvement

### 3. **Actionable Suggestions**
Enhancement results include specific, actionable improvement suggestions:

```python
result.suggestions  # List of improvement recommendations
```

### 4. **Graceful Degradation**
If Gemini API is not available or configured:

- Service returns `is_available() == False`
- All endpoints return helpful error messages
- Application continues working without enhancement features
- No breaking changes to existing functionality

### 5. **Batch Processing**
Process multiple items efficiently:

```python
# Enhance 10 code snippets in one batch
results = integration.batch_enhance([code1, code2, ...], "code_quality", "javascript")
```

---

## 🚀 Quick Start

### 1. **Prerequisites**

```bash
# Install Gemini client
pip install google-generativeai

# Set API key
export GOOGLE_API_KEY="your_api_key_here"
```

### 2. **Basic Usage**

```python
from src.backend.base.langflow.custom.gemini.service import GeminiIntegration

# Initialize
integration = GeminiIntegration()

# Clean a prompt
result = integration.clean_prompt("Generate React button")

# Check results
print(f"Original: {result.original_content}")
print(f"Enhanced: {result.enhanced_content}")
print(f"Quality: {result.quality_score_before} → {result.quality_score_after}")
print(f"Suggestions: {result.suggestions}")
```

### 3. **API Usage**

```bash
# Clean a prompt
curl -X POST http://localhost:8000/api/v1/gemini/enhance/prompt \
  -H "Content-Type: application/json" \
  -d '{"content": "Generate button"}'

# Enhance code
curl -X POST http://localhost:8000/api/v1/gemini/enhance/code/quality \
  -H "Content-Type: application/json" \
  -d '{"code": "x=1", "language": "python"}'

# Check if available
curl http://localhost:8000/api/v1/gemini/health
```

---

## 📚 API Reference

### Enhancement Endpoints

#### **POST `/api/v1/gemini/enhance/prompt`**
Clean and optimize prompts for better AI responses.

**Request:**
```json
{
  "content": "Generate a button component",
  "system_instruction": "You are a prompt optimization expert",
  "model": "gemini-2.5-pro"
}
```

**Response:**
```json
{
  "enhancement_type": "prompt_clean",
  "original_content": "Generate a button component",
  "enhanced_content": "Generate a highly reusable, accessible React button component...",
  "quality_score_before": 0.6,
  "quality_score_after": 0.92,
  "suggestions": [
    "Add specificity about component requirements",
    "Mention accessibility considerations",
    "Include styling guidelines"
  ],
  "status": "SUCCESS",
  "tokens_used": 245
}
```

#### **POST `/api/v1/gemini/enhance/code/quality`**
Improve code structure and best practices.

**Request:**
```json
{
  "code": "x = 1\nprint(x)",
  "language": "python"
}
```

**Response:**
```json
{
  "enhancement_type": "code_quality",
  "original_content": "x = 1\nprint(x)",
  "enhanced_content": "#!/usr/bin/env python\n\"\"\"Module docstring.\"\"\"\n\ndef main():\n    \"\"\"Main function.\"\"\"\n    value = 1\n    print(value)\n\nif __name__ == \"__main__\":\n    main()",
  "quality_score_before": 0.3,
  "quality_score_after": 0.85,
  "suggestions": [
    "Add module docstring",
    "Use descriptive variable names (value instead of x)",
    "Wrap main logic in function",
    "Add main guard"
  ],
  "status": "SUCCESS"
}
```

#### **POST `/api/v1/gemini/enhance/accessibility`**
Enhance WCAG compliance and inclusive design.

**Request:**
```json
{
  "code": "<button onclick=\"handleClick()\">Click</button>",
  "language": "html"
}
```

**Response:**
```json
{
  "enhancement_type": "accessibility",
  "original_content": "<button onclick=\"handleClick()\">Click</button>",
  "enhanced_content": "<button\n  aria-label=\"Perform action\"\n  role=\"button\"\n  onClick={handleClick}\n  onKeyDown={(e) => e.key === 'Enter' && handleClick()}\n>Click</button>",
  "suggestions": [
    "Add aria-label for screen readers",
    "Add keyboard navigation (Enter key)",
    "Use semantic HTML",
    "Ensure sufficient color contrast"
  ],
  "status": "SUCCESS"
}
```

#### **POST `/api/v1/gemini/enhance/performance`**
Optimize algorithms and resource usage.

**Request:**
```json
{
  "code": "const result = [].concat(...arrays);",
  "language": "javascript"
}
```

**Response:**
```json
{
  "enhancement_type": "performance",
  "original_content": "const result = [].concat(...arrays);",
  "enhanced_content": "const result = arrays.flat();",
  "suggestions": [
    "Use Array.flat() for better performance with nested arrays",
    "Reduces memory allocations",
    "More readable modern syntax"
  ],
  "status": "SUCCESS"
}
```

#### **POST `/api/v1/gemini/enhance/security`**
Detect and fix security vulnerabilities.

**Request:**
```json
{
  "code": "db.query(\"SELECT * FROM users WHERE id = \" + userId)",
  "language": "python"
}
```

**Response:**
```json
{
  "enhancement_type": "security",
  "original_content": "db.query(\"SELECT * FROM users WHERE id = \" + userId)",
  "enhanced_content": "db.query(\"SELECT * FROM users WHERE id = %s\", (userId,))",
  "suggestions": [
    "VULNERABILITY: SQL Injection detected",
    "Use parameterized queries",
    "Sanitize user inputs",
    "Implement input validation"
  ],
  "status": "SUCCESS"
}
```

#### **POST `/api/v1/gemini/enhance/documentation`**
Generate comprehensive documentation.

**Request:**
```json
{
  "code": "export const Button = ({ label, onClick }) => { return <button onClick={onClick}>{label}</button>; }",
  "language": "javascript"
}
```

**Response:**
```json
{
  "enhancement_type": "documentation",
  "enhanced_content": "/**\n * Button component for user interactions.\n * @component\n * @param {Object} props - Component props\n * @param {string} props.label - Button label text\n * @param {Function} props.onClick - Callback on button click\n * @returns {JSX.Element} Button component\n */\nexport const Button = ({ label, onClick }) => { ... }",
  "suggestions": [
    "Added JSDoc comments",
    "Documented all parameters",
    "Added return type documentation",
    "Included component marker"
  ],
  "status": "SUCCESS"
}
```

#### **POST `/api/v1/gemini/enhance/batch`**
Process multiple items efficiently.

**Request:**
```json
{
  "items": [
    "Generate button",
    "x = 1",
    "const x = y || 0"
  ],
  "enhancement_type": "code_quality",
  "language": "javascript"
}
```

**Response:**
```json
{
  "total_items": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    { "original": "Generate button", "enhanced": "...", "status": "SUCCESS" },
    { "original": "x = 1", "enhanced": "...", "status": "SUCCESS" },
    { "original": "const x = y || 0", "enhanced": "...", "status": "SUCCESS" }
  ],
  "average_improvement": 0.45
}
```

### Configuration Endpoints

#### **GET `/api/v1/gemini/config`**
Check Gemini configuration status.

**Response:**
```json
{
  "is_available": true,
  "api_key_configured": true,
  "models_available": ["gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-pro"],
  "enhancement_types_available": 6
}
```

#### **GET `/api/v1/gemini/health`**
Check service health and availability.

**Response:**
```json
{
  "status": "healthy",
  "service_available": true,
  "api_key_set": true,
  "message": "Gemini integration ready"
}
```

#### **GET `/api/v1/gemini/models`**
List available Gemini models.

**Response:**
```json
{
  "models": [
    {
      "id": "gemini-2.5-pro",
      "name": "Gemini 2.5 Pro",
      "description": "Most advanced model (recommended)"
    },
    {
      "id": "gemini-2.0-flash",
      "name": "Gemini 2.0 Flash",
      "description": "Fast model for quick operations"
    },
    {
      "id": "gemini-1.5-pro",
      "name": "Gemini 1.5 Pro",
      "description": "Reliable model with good balance"
    }
  ]
}
```

#### **GET `/api/v1/gemini/enhancement-types`**
List available enhancement types.

**Response:**
```json
{
  "types": [
    {
      "id": "prompt_clean",
      "name": "Prompt Cleaning",
      "description": "Optimize and refine AI prompts"
    },
    {
      "id": "code_quality",
      "name": "Code Quality",
      "description": "Improve code structure and practices"
    },
    {
      "id": "accessibility",
      "name": "Accessibility",
      "description": "Enhance WCAG compliance"
    },
    {
      "id": "performance",
      "name": "Performance",
      "description": "Optimize algorithms and resources"
    },
    {
      "id": "security",
      "name": "Security",
      "description": "Detect and fix vulnerabilities"
    },
    {
      "id": "documentation",
      "name": "Documentation",
      "description": "Generate comprehensive docs"
    }
  ]
}
```

#### **GET `/api/v1/gemini/info`**
Get integration information and capabilities.

**Response:**
```json
{
  "integration_name": "Gemini 2.5 Pro",
  "version": "1.0.0",
  "capabilities": [
    "prompt_optimization",
    "code_quality_improvement",
    "accessibility_enhancement",
    "performance_optimization",
    "security_analysis",
    "documentation_generation"
  ],
  "supported_languages": ["python", "javascript", "typescript", "jsx", "tsx", "html", "css", "sql"],
  "batch_processing": true,
  "max_batch_size": 50,
  "documentation_url": "/docs/gemini"
}
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
export GOOGLE_API_KEY="your_google_api_key"

# Optional (with defaults)
export GEMINI_MODEL="gemini-2.5-pro"
export GEMINI_TEMPERATURE="0.7"
export GEMINI_MAX_TOKENS="2048"
```

### API Key Setup

1. **Get API Key:**
   ```bash
   # Visit Google AI Studio
   https://aistudio.google.com/app/apikeys
   ```

2. **Set Environment Variable:**
   ```bash
   # macOS/Linux
   export GOOGLE_API_KEY="your_key_here"
   
   # or add to .env
   echo 'GOOGLE_API_KEY="your_key_here"' >> .env
   ```

3. **Verify Configuration:**
   ```bash
   curl http://localhost:8000/api/v1/gemini/health
   ```

---

## 💻 Code Examples

### Example 1: Enhance React Component

```python
from src.backend.base.langflow.custom.gemini.service import GeminiIntegration

integration = GeminiIntegration()

jsx_code = """
export const Button = ({ label, onClick }) => {
  return <button onClick={onClick}>{label}</button>;
};
"""

# Enhance code quality
result = integration.enhance_code_quality(jsx_code, "javascript")

print(f"✨ Enhanced Code:\n{result.enhanced_content}")
print(f"📊 Quality: {result.quality_score_before:.1%} → {result.quality_score_after:.1%}")
print(f"💡 Suggestions:\n" + "\n".join(f"  • {s}" for s in result.suggestions))
```

### Example 2: Add Accessibility

```python
integration = GeminiIntegration()

html_code = "<button onclick='handleClick()'>Click me</button>"

result = integration.enhance_accessibility(html_code, "html")

print(result.enhanced_content)
# Output: <button aria-label="..." role="button" onClick={...}>...</button>
```

### Example 3: Security Analysis

```python
integration = GeminiIntegration()

vulnerable_sql = "SELECT * FROM users WHERE id = " + user_id

result = integration.enhance_security(vulnerable_sql, "python")

if "VULNERABILITY" in str(result.suggestions):
    print("🚨 Security issue detected!")
    print(result.enhanced_content)
```

### Example 4: Batch Processing

```python
integration = GeminiIntegration()

code_snippets = [
    "x = 1",
    "const arr = [1, 2, 3]",
    "function test() { return x; }",
]

results = integration.batch_enhance(
    code_snippets,
    enhancement_type="code_quality",
    language="javascript"
)

for i, result in enumerate(results):
    print(f"Item {i+1}: {result.quality_score_before:.1%} → {result.quality_score_after:.1%}")
```

### Example 5: Check Availability

```python
from src.backend.base.langflow.custom.gemini.service import GeminiIntegration

if GeminiIntegration.is_available():
    integration = GeminiIntegration()
    result = integration.clean_prompt("your prompt")
else:
    print("Gemini API not configured")
```

---

## 📊 Quality Metrics

### Quality Score Calculation

Quality scores (0-1) are calculated based on:

**For Prompts:**
- ✓ Specificity and clarity
- ✓ Domain expertise indicators
- ✓ Completeness of requirements
- ✓ Use of best practices

**For Code:**
- ✓ Code complexity (cyclomatic complexity)
- ✓ Comments and documentation
- ✓ Error handling presence
- ✓ Best practices adherence

### Interpreting Results

```
Score: 0.0 - 0.3    ⚠️  Needs significant improvement
Score: 0.3 - 0.6    📝 Good room for improvement
Score: 0.6 - 0.8    ✅ Good quality
Score: 0.8 - 1.0    ⭐ Excellent quality
```

---

## 🛡️ Error Handling

### Graceful Degradation

If Gemini is not configured:

```python
from src.backend.base.langflow.custom.gemini.service import GeminiIntegration

if not GeminiIntegration.is_available():
    # Handle gracefully
    print("Gemini enhancement layer not available")
    # Application continues with existing features
```

### Common Errors

**Missing API Key:**
```
{
  "error": "GOOGLE_API_KEY not configured",
  "status": "FAILED",
  "message": "Please set GOOGLE_API_KEY environment variable"
}
```

**API Rate Limit:**
```
{
  "error": "Rate limit exceeded",
  "status": "FAILED",
  "message": "API rate limit exceeded. Try again later."
}
```

**Empty Content:**
```
{
  "error": "Empty content provided",
  "status": "FAILED",
  "message": "Content cannot be empty"
}
```

---

## 📈 Performance Considerations

### Batch Processing Benefits

```python
# ❌ Inefficient - 3 API calls
result1 = integration.enhance_code_quality(code1, "javascript")
result2 = integration.enhance_code_quality(code2, "javascript")
result3 = integration.enhance_code_quality(code3, "javascript")

# ✅ Efficient - 1 API call
results = integration.batch_enhance([code1, code2, code3], "code_quality", "javascript")
```

### Token Usage

Each enhancement uses API tokens:

```python
result = integration.enhance_code_quality(code, "javascript")
print(f"Tokens used: {result.tokens_used}")
print(f"Input tokens: {result.input_tokens}")
print(f"Output tokens: {result.output_tokens}")
```

---

## 🧪 Testing

### Run Unit Tests

```bash
# Run all Gemini tests
pytest tests/unit/custom/test_gemini_integration.py -v

# Run specific test class
pytest tests/unit/custom/test_gemini_integration.py::TestEnhancementTypes -v

# Run with coverage
pytest tests/unit/custom/test_gemini_integration.py --cov=src/backend/base/langflow/custom/gemini
```

### Test Categories

- **Configuration Tests** - API key validation
- **Enhancement Type Tests** - Enum validation
- **Helper Method Tests** - Internal function testing
- **Integration Tests** - Full enhancement workflows
- **Error Handling Tests** - Exception scenarios
- **Edge Cases** - Boundary conditions

---

## 📦 Integration Points

### With Framer Component Generator (Task 4)

```python
# Generate Framer component
framer_code = framer_service.generate_wrapper(jsx_component)

# Enhance the generated code
enhanced = gemini_integration.enhance_code_quality(framer_code, "javascript")

# Deploy enhanced component
```

### With Local Runtimes (Task 3)

```python
# Generate code locally (Task 3)
code = local_runtime.generate(prompt)

# Enhance with Gemini (Task 5)
enhanced = gemini_integration.enhance_code_quality(code, "javascript")

# Return to user
```

### With Orchestrator (Task 2)

```python
# Orchestrate multi-step process
1. Generate with CodeLlama
2. Enhance with Gemini
3. Optimize for Framer
4. Deploy to canvas
```

---

## 🎓 Advanced Usage

### Custom Enhancement Strategy

```python
integration = GeminiIntegration()

# Combine multiple enhancements
code = """
const Button = ({ label, onClick }) => {
  return <button onClick={onClick}>{label}</button>;
};
"""

# 1. Improve quality
quality_result = integration.enhance_code_quality(code, "javascript")

# 2. Add accessibility
accessibility_result = integration.enhance_accessibility(quality_result.enhanced_content, "javascript")

# 3. Add documentation
docs_result = integration.add_documentation(accessibility_result.enhanced_content, "javascript")

final_code = docs_result.enhanced_content
```

### Conditional Enhancement

```python
result = integration.enhance_code_quality(code, "javascript")

if result.quality_score_after - result.quality_score_before > 0.3:
    # Use enhanced version
    use_code = result.enhanced_content
else:
    # Keep original
    use_code = code
```

---

## 📝 Troubleshooting

### Issue: "GOOGLE_API_KEY not set"

**Solution:**
```bash
export GOOGLE_API_KEY="your_key_here"
# Restart your application
```

### Issue: "Rate limit exceeded"

**Solution:**
- Implement request throttling
- Use batch processing instead of individual calls
- Wait before retrying

### Issue: "Model not available"

**Solution:**
```python
# Check available models
from src.backend.base.langflow.custom.gemini.service import GeminiModel

# Use fallback model
result = integration.clean_prompt(
    content="...",
    model=GeminiModel.GEMINI_2_0_FLASH  # Faster but less powerful
)
```

---

## 🔗 Related Documentation

- [Task 4: Framer Component Generator](./TASK4_FRAMER_DOCS.md)
- [Task 3: Local Model Runtimes](./TASK3_LOCAL_RUNTIMES.md)
- [Task 2: Multi-Step Orchestrator](./DEVELOPMENT.md)
- [Task 1: CRUD APIs](./README.md)

---

## 📞 Support

For issues or questions:

1. Check the **Troubleshooting** section above
2. Review example code in **Code Examples**
3. Run tests with `pytest` to verify installation
4. Check API health: `curl http://localhost:8000/api/v1/gemini/health`

---

**Version:** 1.0.0  
**Last Updated:** December 2024  
**Status:** ✅ Production Ready
