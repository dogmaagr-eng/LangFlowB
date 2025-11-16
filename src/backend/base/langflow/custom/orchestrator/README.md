# Orchestrator API

El **Orchestrator** es el engine central que ejecuta pipelines multi-modelo. Permite orquestar agentes especializados (CodeLlama, CodeGemma, T5Gemma) en pasos aislados, capturar artefactos intermedios, y ejecutar un modelo "Assembler" final que limpia, pulenta y combina los outputs siguiendo el patrón "Lego".

## Conceptos Clave

### Pipeline (Tubería)
Una secuencia de **pasos** que se ejecutan secuencialmente. Cada paso:
- Usa un modelo específico
- Recibe un prompt y contexto
- Genera output y artefactos
- Alimenta el contexto para el siguiente paso

### Pasos Aislados
Cada paso es **independiente** y usa su propio modelo:
- **CodeLlama**: Análisis, generación inicial, planificación
- **CodeGemma**: Refinamiento, optimización, bug fixing
- **T5Gemma**: Transformaciones, refactorización, documentación
- **Assembler**: Combina y limpia outputs finales (ejecutado automáticamente)

### Patrón "Lego"
El Assembler combina los artefactos como piezas de Lego:
- Cada pieza es un componente funcional
- Se ensamblan sin conflictos
- Se validan y optimizan
- Se producen con documentación completa

### Contexto Persistente
Cada paso tiene acceso a:
- Contexto global (configuración del proyecto)
- Salidas de pasos anteriores
- Artefactos intermedios

---

## Endpoints

### Ejecutar Pipeline
```
POST /api/v1/orchestrator/projects/{project_id}/execute
```

**Request Body:**
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "React Component Pipeline",
  "steps": [
    {
      "step_name": "analyze_requirements",
      "model_type": "CodeLlama",
      "prompt": "Analyze the component requirements and create a design plan",
      "context": {
        "component_type": "Form",
        "fields": ["name", "email", "submit"]
      },
      "parameters": {
        "max_tokens": 512,
        "temperature": 0.7
      }
    },
    {
      "step_name": "generate_component",
      "model_type": "CodeGemma",
      "prompt": "Generate a well-structured React component based on the design plan",
      "parameters": {
        "max_tokens": 1024,
        "temperature": 0.5
      }
    },
    {
      "step_name": "optimize_code",
      "model_type": "T5Gemma",
      "prompt": "Optimize and refactor the component code for production",
      "parameters": {
        "max_tokens": 512,
        "temperature": 0.3
      }
    }
  ],
  "global_context": {
    "framework": "react",
    "version": "18.0",
    "styling": "tailwind"
  },
  "metadata": {
    "priority": "high",
    "deadline": "2025-11-20"
  }
}
```

**Response (202 Accepted):**
```json
{
  "run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "steps": [
    {
      "step_name": "analyze_requirements",
      "status": "SUCCESS",
      "result": "Design plan for form component...",
      "artifacts": [],
      "execution_time": 2.5
    },
    {
      "step_name": "generate_component",
      "status": "SUCCESS",
      "result": "Generated React component code...",
      "artifacts": [
        {
          "type": "jsx",
          "name": "generate_component_component_0.jsx",
          "content": "export default function Form() { ... }"
        }
      ],
      "execution_time": 3.2
    },
    {
      "step_name": "optimize_code",
      "status": "SUCCESS",
      "result": "Optimized component code...",
      "artifacts": [
        {
          "type": "jsx",
          "name": "optimize_code_component_0.jsx",
          "content": "export default function Form() { ... }"
        }
      ],
      "execution_time": 1.8
    }
  ],
  "final_artifacts": [
    {
      "type": "jsx",
      "name": "Form.jsx",
      "content": "Final, production-ready component..."
    }
  ],
  "assembled_code": "Complete assembled and polished code...",
  "started_at": "2025-11-16T10:30:00Z",
  "finished_at": "2025-11-16T10:30:10Z"
}
```

---

### Obtener Resumen de Ejecución
```
GET /api/v1/orchestrator/runs/{run_id}
```

**Response:**
```json
{
  "run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "total_steps": 3,
  "successful_steps": 3,
  "failed_steps": 0,
  "total_execution_time": 7.5,
  "steps": [
    {
      "step_name": "analyze_requirements",
      "status": "SUCCESS",
      "result": "...",
      "artifacts": [],
      "execution_time": 2.5
    },
    ...
  ]
}
```

---

### Listar Modelos Disponibles
```
GET /api/v1/orchestrator/models
```

**Response:**
```json
{
  "models": [
    {
      "name": "CodeLlama",
      "description": "Meta's CodeLlama - Code generation and understanding",
      "capabilities": ["code_generation", "code_analysis", "refactoring"],
      "recommended_for": ["Initial analysis", "Code generation"]
    },
    {
      "name": "CodeGemma",
      "description": "Google's CodeGemma - Specialized code model",
      "capabilities": ["code_generation", "code_explanation", "bug_fixing"],
      "recommended_for": ["Code refinement", "Bug fixing"]
    },
    {
      "name": "T5Gemma",
      "description": "T5Gemma - Text-to-text transfer transformer",
      "capabilities": ["text_transformation", "summarization", "translation"],
      "recommended_for": ["Code transformation", "Documentation generation"]
    },
    {
      "name": "Assembler",
      "description": "Final assembly model - Combines and polishes outputs",
      "capabilities": ["code_assembly", "optimization", "validation"],
      "recommended_for": ["Final assembly (automatic)"]
    }
  ]
}
```

---

### Listar Plantillas de Pipeline
```
GET /api/v1/orchestrator/templates
```

**Response:**
```json
{
  "templates": [
    {
      "name": "React Component Pipeline",
      "description": "Generate production-ready React components",
      "steps": [
        {
          "step_name": "analyze_requirements",
          "model_type": "CodeLlama",
          "prompt": "Analyze the component requirements and create a design plan"
        },
        {
          "step_name": "generate_component",
          "model_type": "CodeGemma",
          "prompt": "Generate a well-structured React component based on the design plan"
        },
        {
          "step_name": "optimize_code",
          "model_type": "T5Gemma",
          "prompt": "Optimize and refactor the component code for production"
        }
      ]
    },
    ...
  ]
}
```

---

## Flujo de Ejecución

```
┌─────────────────────────────────────────────────────────────────┐
│                     Pipeline Execution Flow                      │
└─────────────────────────────────────────────────────────────────┘

1. Client → POST /orchestrator/projects/{id}/execute
                 ↓
2. Crear OrchestrationRun (status=PENDING)
                 ↓
3. Para cada paso (secuencial):
   ┌─────────────────────────────────────────┐
   │ Step Input:                              │
   │ - step_name, model_type, prompt         │
   │ - context (del paso anterior)           │
   │ - parameters (max_tokens, temp)         │
   └─────────────────────────────────────────┘
                 ↓
   ┌─────────────────────────────────────────┐
   │ Ejecutar Modelo:                        │
   │ - CodeLlama / CodeGemma / T5Gemma      │
   │ - Inyectar contexto en el prompt        │
   │ - Generar output                        │
   └─────────────────────────────────────────┘
                 ↓
   ┌─────────────────────────────────────────┐
   │ Extraer Artefactos:                    │
   │ - JSX, TSX, CSS, Python                │
   │ - Guardar en BD                        │
   │ - Agregar a contexto siguiente         │
   └─────────────────────────────────────────┘
                 ↓
4. Ejecutar Assembler (modelo especial):
   - Input: todos los outputs + artefactos
   - Output: código limpio, optimizado, final
                 ↓
5. Guardar resultado en BD
   - Actualizar OrchestrationRun (status=SUCCESS/FAILED)
   - Guardar GeneratedArtifacts finales
                 ↓
6. Response → Client (202 Accepted + resultados)
```

---

## Flujo de Contexto

```
Global Context (proyecto):
{
  "framework": "react",
  "version": "18.0",
  "styling": "tailwind"
}
        ↓
Step 1 (CodeLlama):
Input: prompt + global_context
Output: design_plan
Contexto para Step 2: {...global, step_0_output, step_0_artifacts}
        ↓
Step 2 (CodeGemma):
Input: prompt + contexto_step_1 + step_0_output
Output: component_code
Contexto para Step 3: {..., step_1_output, step_1_artifacts}
        ↓
Step 3 (T5Gemma):
Input: prompt + contexto_step_2 + step_1_output
Output: optimized_code
Contexto para Assembler: {..., todos_los_outputs}
        ↓
Assembler:
Input: prompt + todos_contextos + todos_artefactos
Output: final_assembled_code
```

---

## Ejemplos con cURL

### Ejecutar un pipeline simple
```bash
curl -X POST http://localhost:7860/api/v1/orchestrator/projects/550e8400-e29b-41d4-a716-446655440000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Simple Pipeline",
    "steps": [
      {
        "step_name": "analyze",
        "model_type": "CodeLlama",
        "prompt": "Analyze the requirements"
      },
      {
        "step_name": "generate",
        "model_type": "CodeGemma",
        "prompt": "Generate production code"
      }
    ]
  }'
```

### Obtener resumen de ejecución
```bash
curl http://localhost:7860/api/v1/orchestrator/runs/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Obtener modelos disponibles
```bash
curl http://localhost:7860/api/v1/orchestrator/models
```

### Obtener plantillas
```bash
curl http://localhost:7860/api/v1/orchestrator/templates
```

---

## Parámetros de Pasos

### Parámetros Globales
- `max_tokens` (int, default=512): Longitud máxima de output
- `temperature` (float, 0-1, default=0.7): Creatividad/determinismo (0=determinista, 1=creativo)

### Recomendaciones por Etapa
- **Análisis** (CodeLlama): temp=0.7, tokens=512
- **Generación** (CodeGemma): temp=0.5, tokens=1024
- **Optimización** (T5Gemma): temp=0.3, tokens=512
- **Assembler** (automático): temp=0.3, tokens=2048

---

## Códigos de Estado HTTP

| Código | Significado |
|--------|-------------|
| 202    | Accepted (pipeline iniciado) |
| 200    | OK (información recuperada) |
| 404    | Not Found (proyecto/run no existe) |
| 500    | Internal Server Error (fallo en ejecución) |

---

## Manejo de Errores

Si un paso falla:
1. La ejecución se detiene
2. El OrchestrationRun pasa a status=FAILED
3. Se retorna el error en la respuesta
4. Los artefactos hasta ese punto se guardan

Ejemplo de fallo:
```json
{
  "status": "FAILED",
  "error": "Pipeline stopped at step 'generate': Model execution timeout",
  "steps": [
    {
      "step_name": "analyze",
      "status": "SUCCESS",
      ...
    },
    {
      "step_name": "generate",
      "status": "FAILED",
      "error": "Model execution timeout"
    }
  ]
}
```

---

## Tests

```bash
pytest tests/unit/custom/test_orchestrator_simple.py -v
```

Todos los tests pasan: 11/11 ✅

---

## Notas de Implementación

- **Ejecución Secuencial**: Los pasos se ejecutan uno por uno, no en paralelo
- **Contexto Dinámico**: El contexto se enriquece con cada paso
- **Artefactos Automáticos**: Se extraen y guardan automáticamente de los outputs
- **Assembler Automático**: Se ejecuta siempre al final si todos los pasos son exitosos
- **Placeholders**: Si HFModelManager no está disponible, usa placeholders para testing
- **Persistencia**: Todos los resultados se guardan en BD (OrchestrationRun, GeneratedArtifact)
