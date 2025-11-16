# Project CRUD APIs

Este módulo proporciona una API REST completa para gestionar proyectos, contexto, ejecuciones de orquestación y artefactos generados.

## Endpoints

Todos los endpoints están disponibles bajo el prefijo `/api/v1/projects`.

### Proyectos (Projects)

#### Crear Proyecto
```
POST /api/v1/projects/
```

**Request Body:**
```json
{
  "name": "Mi Proyecto",
  "description": "Descripción opcional",
  "metadata": {"clave": "valor"}
}
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Mi Proyecto",
  "description": "Descripción opcional",
  "metadata": {"clave": "valor"},
  "created_at": "2025-11-16T10:00:00Z",
  "updated_at": "2025-11-16T10:00:00Z"
}
```

#### Listar Proyectos
```
GET /api/v1/projects/?skip=0&limit=10
```

**Query Parameters:**
- `skip` (int, default=0): Número de registros a saltar
- `limit` (int, default=10): Máximo número de registros a retornar (máximo 100)

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Proyecto 1",
    "description": "...",
    "metadata": {...},
    "created_at": "2025-11-16T10:00:00Z",
    "updated_at": "2025-11-16T10:00:00Z"
  },
  ...
]
```

#### Obtener Proyecto
```
GET /api/v1/projects/{project_id}
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Mi Proyecto",
  "description": "...",
  "metadata": {...},
  "created_at": "2025-11-16T10:00:00Z",
  "updated_at": "2025-11-16T10:00:00Z"
}
```

#### Actualizar Proyecto
```
PUT /api/v1/projects/{project_id}
```

**Request Body:**
```json
{
  "name": "Nuevo Nombre (opcional)",
  "description": "Nueva descripción (opcional)",
  "metadata": {"nueva_clave": "nuevo_valor"}
}
```

**Response (200):** Proyecto actualizado

#### Eliminar Proyecto
```
DELETE /api/v1/projects/{project_id}
```

**Response (204):** Sin contenido (éxito)

---

### Contexto (Context)

El contexto es información persistente asociada a un proyecto (variables de entorno, configuración, etc.).

#### Crear Contexto
```
POST /api/v1/projects/{project_id}/context
```

**Request Body:**
```json
{
  "key": "database_url",
  "value": "sqlite:///db.sqlite3"
}
```

**Response (201):** Entrada de contexto creada

#### Listar Contexto de Proyecto
```
GET /api/v1/projects/{project_id}/context?skip=0&limit=100
```

**Response (200):** Lista de entradas de contexto

#### Obtener Entrada de Contexto
```
GET /api/v1/projects/context/{context_id}
```

**Response (200):** Entrada de contexto

#### Actualizar Contexto
```
PUT /api/v1/projects/context/{context_id}
```

**Request Body:**
```json
{
  "key": "new_key (opcional)",
  "value": "new_value (opcional)"
}
```

**Response (200):** Entrada actualizada

#### Eliminar Contexto
```
DELETE /api/v1/projects/context/{context_id}
```

**Response (204):** Sin contenido (éxito)

---

### Ejecuciones de Orquestación (Orchestration Runs)

Representa una ejecución del pipeline de orquestación de agentes.

#### Crear Ejecución
```
POST /api/v1/projects/{project_id}/runs
```

**Request Body:**
```json
{
  "status": "PENDING",
  "steps": {
    "step_1": "CodeLlama",
    "step_2": "CodeGemma",
    "step_3": "Assembler"
  }
}
```

**Response (201):** Ejecución creada

#### Listar Ejecuciones del Proyecto
```
GET /api/v1/projects/{project_id}/runs?skip=0&limit=50
```

**Response (200):** Lista de ejecuciones

#### Obtener Ejecución
```
GET /api/v1/projects/runs/{run_id}
```

**Response (200):** Detalles de la ejecución

#### Actualizar Ejecución
```
PUT /api/v1/projects/runs/{run_id}
```

**Request Body:**
```json
{
  "status": "RUNNING",
  "finished": false
}
```

**Response (200):** Ejecución actualizada

#### Eliminar Ejecución
```
DELETE /api/v1/projects/runs/{run_id}
```

**Response (204):** Sin contenido (se eliminan también sus artefactos)

---

### Artefactos Generados (Generated Artifacts)

Código JSX/TSX generado, componentes, y otros artefactos producidos durante la orquestación.

#### Crear Artefacto
```
POST /api/v1/projects/{project_id}/artifacts
```

**Request Body:**
```json
{
  "name": "Button.jsx",
  "path": "/artifacts/Button.jsx",
  "content": "export default function Button() { return <button>Click me</button>; }",
  "metadata": {"type": "framer", "framework": "react"},
  "run_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (201):** Artefacto creado

#### Listar Artefactos del Proyecto
```
GET /api/v1/projects/{project_id}/artifacts?skip=0&limit=100
```

**Response (200):** Lista de artefactos

#### Listar Artefactos de una Ejecución
```
GET /api/v1/projects/runs/{run_id}/artifacts?skip=0&limit=100
```

**Response (200):** Lista de artefactos de esa ejecución

#### Obtener Artefacto
```
GET /api/v1/projects/artifacts/{artifact_id}
```

**Response (200):** Detalles del artefacto

#### Actualizar Artefacto
```
PUT /api/v1/projects/artifacts/{artifact_id}
```

**Request Body:**
```json
{
  "name": "Button_v2.jsx",
  "content": "export default function Button() { return <button>Updated</button>; }",
  "metadata": {"version": 2}
}
```

**Response (200):** Artefacto actualizado

#### Eliminar Artefacto
```
DELETE /api/v1/projects/artifacts/{artifact_id}
```

**Response (204):** Sin contenido (éxito)

---

## Códigos de Estado HTTP

| Código | Significado |
|--------|-------------|
| 200    | OK (éxito) |
| 201    | Created (recurso creado) |
| 204    | No Content (éxito, sin cuerpo de respuesta) |
| 400    | Bad Request (solicitud inválida) |
| 404    | Not Found (recurso no encontrado) |
| 500    | Internal Server Error (error del servidor) |

---

## Ejemplos con cURL

### Crear un proyecto
```bash
curl -X POST http://localhost:7860/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Aplicación",
    "description": "Aplicación de prueba",
    "metadata": {"env": "development"}
  }'
```

### Listar proyectos
```bash
curl http://localhost:7860/api/v1/projects/
```

### Obtener un proyecto específico
```bash
curl http://localhost:7860/api/v1/projects/550e8400-e29b-41d4-a716-446655440000
```

### Crear contexto para un proyecto
```bash
curl -X POST http://localhost:7860/api/v1/projects/550e8400-e29b-41d4-a716-446655440000/context \
  -H "Content-Type: application/json" \
  -d '{
    "key": "api_key",
    "value": "sk-xxxxxxxxxxxxx"
  }'
```

### Crear una ejecución de orquestación
```bash
curl -X POST http://localhost:7860/api/v1/projects/550e8400-e29b-41d4-a716-446655440000/runs \
  -H "Content-Type: application/json" \
  -d '{
    "status": "PENDING",
    "steps": {
      "analysis": "CodeLlama",
      "generation": "CodeGemma",
      "assembly": "T5Gemma"
    }
  }'
```

---

## Integración con Frontend

Los endpoints pueden ser consumidos desde un cliente frontend (React, Vue, etc.) usando `fetch` o librerías como `axios`:

### Ejemplo con JavaScript/React
```javascript
// Crear un proyecto
const response = await fetch('http://localhost:7860/api/v1/projects/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Mi Proyecto',
    description: 'Descripción'
  })
});
const project = await response.json();
console.log('Proyecto creado:', project.id);

// Listar proyectos
const projectsRes = await fetch('http://localhost:7860/api/v1/projects/');
const projects = await projectsRes.json();
console.log('Proyectos:', projects);
```

---

## Tests Unitarios

Los tests están en `tests/unit/custom/test_projects_crud.py`. Ejecutar:

```bash
pytest tests/unit/custom/test_projects_crud.py -v
```

---

## Notas de Implementación

- **Cascada de eliminación**: Al eliminar un proyecto, se eliminan automáticamente su contexto, ejecuciones y artefactos.
- **Timestamps**: `created_at` y `updated_at` se generan automáticamente en UTC.
- **UUIDs**: Todos los IDs son identificadores únicos universales (UUID v4).
- **Paginación**: Usar `skip` y `limit` para navegar grandes conjuntos de datos.
- **Validación**: El backend valida automáticamente los datos de entrada (longitudes de string, tipos de datos, etc.).
