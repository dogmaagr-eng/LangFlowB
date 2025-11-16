# TASK 5: GEMINI 2.5 PRO INTEGRATION - QUICKSTART

**Version:** 1.0.0  
**Status:** ✅ Production Ready  
**Time to Setup:** 5 minutes  

---

## ⚡ 5-Minute Setup

### Step 1: Get Gemini API Key (2 min)

```bash
# Visit Google AI Studio
open https://aistudio.google.com/app/apikeys

# Copy your API key
# Format: AIzaSy...
```

### Step 2: Set Environment Variable (1 min)

```bash
# Option A: Export in terminal (session only)
export GOOGLE_API_KEY="your_key_here"

# Option B: Add to .env (persistent)
echo 'GOOGLE_API_KEY="your_key_here"' >> .env

# Option C: Add to shell profile (permanent)
echo 'export GOOGLE_API_KEY="your_key_here"' >> ~/.zshrc
source ~/.zshrc
```

### Step 3: Install Package (1 min)

```bash
pip install google-generativeai
```

### Step 4: Verify Installation (1 min)

```bash
# Start Langflow backend
make backend

# In another terminal, test health check
curl http://localhost:8000/api/v1/gemini/health

# Expected response
{
  "status": "healthy",
  "service_available": true,
  "api_key_set": true
}
```

---

## 🚀 10-Second First Run

### Python Script

```python
from src.backend.base.langflow.custom.gemini.service import GeminiIntegration

# Initialize
gemini = GeminiIntegration()

# Clean a prompt
result = gemini.clean_prompt("Generate button")

# Print results
print(f"✨ Enhanced: {result.enhanced_content}")
print(f"📊 Quality: {result.quality_score_before:.0%} → {result.quality_score_after:.0%}")
```

### API Request

```bash
curl -X POST http://localhost:8000/api/v1/gemini/enhance/prompt \
  -H "Content-Type: application/json" \
  -d '{"content": "Generate button"}'
```

---

## 🎯 Common Use Cases

### 1. Enhance Code Quality

```python
from src.backend.base.langflow.custom.gemini.service import GeminiIntegration

gemini = GeminiIntegration()

jsx_code = """
export const Button = ({ label, onClick }) => {
  return <button onClick={onClick}>{label}</button>;
};
"""

result = gemini.enhance_code_quality(jsx_code, "javascript")

print(result.enhanced_content)
print(f"Quality: {result.quality_score_before:.0%} → {result.quality_score_after:.0%}")
```

### 2. Optimize Prompts

```python
gemini = GeminiIntegration()

prompt = "Generate button"

result = gemini.clean_prompt(prompt)

print(f"Original: {result.original_content}")
print(f"Enhanced: {result.enhanced_content}")
print(f"Suggestions: {result.suggestions}")
```

### 3. Add Accessibility

```python
gemini = GeminiIntegration()

html = "<button onclick='click()'>Click</button>"

result = gemini.enhance_accessibility(html, "html")

print(result.enhanced_content)
```

### 4. Find Security Issues

```python
gemini = GeminiIntegration()

vulnerable_code = "SELECT * FROM users WHERE id = " + user_id

result = gemini.enhance_security(vulnerable_code, "python")

if "VULNERABILITY" in str(result.suggestions):
    print("🚨 Security issue found!")
    print(result.enhanced_content)
```

### 5. Batch Process Multiple Items

```python
gemini = GeminiIntegration()

codes = [
    "x = 1",
    "const arr = []",
    "def test(): pass"
]

results = gemini.batch_enhance(codes, "code_quality", "javascript")

for i, result in enumerate(results):
    print(f"Item {i+1}: {result.quality_score_before:.0%} → {result.quality_score_after:.0%}")
```

---

## 🔌 REST API Quick Reference

### Enhance Prompt
```bash
curl -X POST http://localhost:8000/api/v1/gemini/enhance/prompt \
  -H "Content-Type: application/json" \
  -d '{"content": "your prompt"}'
```

### Enhance Code
```bash
curl -X POST http://localhost:8000/api/v1/gemini/enhance/code/quality \
  -H "Content-Type: application/json" \
  -d '{"code": "your code", "language": "javascript"}'
```

### Add Accessibility
```bash
curl -X POST http://localhost:8000/api/v1/gemini/enhance/accessibility \
  -H "Content-Type: application/json" \
  -d '{"code": "your html", "language": "html"}'
```

### Check Security
```bash
curl -X POST http://localhost:8000/api/v1/gemini/enhance/security \
  -H "Content-Type: application/json" \
  -d '{"code": "your code", "language": "python"}'
```

### Optimize Performance
```bash
curl -X POST http://localhost:8000/api/v1/gemini/enhance/performance \
  -H "Content-Type: application/json" \
  -d '{"code": "your code", "language": "javascript"}'
```

### Generate Documentation
```bash
curl -X POST http://localhost:8000/api/v1/gemini/enhance/documentation \
  -H "Content-Type: application/json" \
  -d '{"code": "your code", "language": "javascript"}'
```

### Check Service Health
```bash
curl http://localhost:8000/api/v1/gemini/health
```

### Get Available Models
```bash
curl http://localhost:8000/api/v1/gemini/models
```

### List Enhancement Types
```bash
curl http://localhost:8000/api/v1/gemini/enhancement-types
```

---

## 🧪 Quick Tests

### Run All Tests

```bash
pytest tests/unit/custom/test_gemini_integration.py -v
```

### Run Specific Test

```bash
pytest tests/unit/custom/test_gemini_integration.py::TestEnhancementTypes -v
```

### Run with Coverage

```bash
pytest tests/unit/custom/test_gemini_integration.py --cov=src/backend/base/langflow/custom/gemini
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Required
GOOGLE_API_KEY="your_api_key"

# Optional (defaults shown)
GEMINI_MODEL="gemini-2.5-pro"
GEMINI_TEMPERATURE="0.7"
GEMINI_MAX_TOKENS="2048"
```

### Check Configuration

```python
from src.backend.base.langflow.custom.gemini.service import GeminiIntegration

# Check if available
if GeminiIntegration.is_available():
    print("✅ Gemini integration available")
else:
    print("❌ Gemini integration not configured")

# Check API key
is_configured, message = GeminiIntegration.check_api_key()
print(f"Configuration: {message}")
```

---

## 🐛 Troubleshooting

### Problem: "GOOGLE_API_KEY not configured"

**Solution:**
```bash
export GOOGLE_API_KEY="your_key"
# Verify
echo $GOOGLE_API_KEY
# Restart backend
make backend
```

### Problem: "Module not found"

**Solution:**
```bash
pip install google-generativeai
python -c "import google.generativeai; print('✅ Installed')"
```

### Problem: "API rate limit"

**Solution:**
- Use batch processing instead
- Add delay between requests
- Wait a few seconds and retry

### Problem: Health check fails

**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/api/v1/health

# Check Gemini specifically
curl http://localhost:8000/api/v1/gemini/health

# View backend logs
make backend  # in new terminal
```

---

## 📊 Quality Scores Explained

**Score Range:**
```
0.0 - 0.3 ⚠️  Needs improvement
0.3 - 0.6 📝 Room for improvement  
0.6 - 0.8 ✅ Good
0.8 - 1.0 ⭐ Excellent
```

**Example:**
```python
result = gemini.enhance_code_quality("x=1", "python")

print(f"Original quality: {result.quality_score_before:.0%}")  # 30%
print(f"Enhanced quality: {result.quality_score_after:.0%}")   # 85%
print(f"Improvement: {(result.quality_score_after - result.quality_score_before)*100:.0f}%")  # 55%
```

---

## 🎓 Learning Path

**Beginner (5 min):**
1. ✅ Setup API key
2. ✅ Run health check
3. ✅ Test prompt cleaning

**Intermediate (15 min):**
1. ✅ Enhance code quality
2. ✅ Check security
3. ✅ View suggestions

**Advanced (30 min):**
1. ✅ Batch processing
2. ✅ Quality metrics
3. ✅ Error handling
4. ✅ Custom workflows

**Expert (1+ hour):**
1. ✅ Multi-enhancement pipelines
2. ✅ Integration with Framer
3. ✅ Performance tuning
4. ✅ Custom enhancement strategies

---

## 📞 Need Help?

### Quick Links
- 📖 [Full Documentation](./TASK5_GEMINI_DOCS.md)
- 🧪 [Test Examples](../tests/unit/custom/test_gemini_integration.py)
- 📋 [Delivery Report](./TASK5_DELIVERY_REPORT.md)

### Check Status
```bash
# Health check
curl http://localhost:8000/api/v1/gemini/health

# Configuration
curl http://localhost:8000/api/v1/gemini/config

# Available types
curl http://localhost:8000/api/v1/gemini/enhancement-types
```

### Debug Mode
```python
from src.backend.base.langflow.custom.gemini.service import GeminiIntegration

# Enable debugging
gemini = GeminiIntegration()

# Check availability
print(f"Available: {GeminiIntegration.is_available()}")

# Check config
is_ok, msg = GeminiIntegration.check_api_key()
print(f"API Key: {is_ok} - {msg}")
```

---

## ✅ Next Steps

1. **Setup:** Complete the 5-minute setup above
2. **Test:** Run `pytest` to verify installation
3. **Explore:** Try the common use cases
4. **Integrate:** Add to your workflow
5. **Deploy:** Ready for production

---

**Status:** ✅ Production Ready  
**Support:** Full documentation available  
**Questions?** Check troubleshooting section above

**Ready to enhance your code? Let's go! 🚀**
