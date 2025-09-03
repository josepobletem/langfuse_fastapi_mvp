
# Langfuse FastAPI Enhanced

Aplicación de ejemplo en **FastAPI** con integración opcional de **Langfuse** para trazabilidad y métricas de **Prometheus** listas para usar.

Incluye:
- **/metrics** con métricas Prometheus (latencia, requests, tokens, etc.)
- **Logs JSON** con `request_id` para trazabilidad en logs centralizados
- **Guardrails**: truncado por palabras y heurística simple de toxicidad
- **Langfuse scores** (`non_empty_answer`, `toxicity_safe`)
- **Tests** con stubs de LLM (no requiere OpenAI en CI)
- **Retries** con backoff en llamadas al LLM
- **Configuración 12-factor** con Pydantic y `.env`

---

## 🚀 Endpoints principales

- **GET `/health`**  
  Devuelve estado de la app, si OpenAI está configurado y si Langfuse está habilitado.

- **GET `/metrics`**  
  Expone métricas Prometheus (para scraping por Prometheus/Grafana).  

- **POST `/ask`**  
  Recibe:
  ```json
  {
    "user_id": "jose",
    "question": "¿Qué es Langfuse?",
    "max_words": 150
  }
  ```
  Responde:
  ```json
  {
    "answer": "...",
    "trace_id": "abc123",
    "generation_id": "gen123",
    "request_id": "req-uuid"
  }
  ```

---

## ⚙️ Instalación y ejecución local

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate      # Windows: .\.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Levantar servidor
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

---

## ✅ Tests

Se usan pruebas unitarias con **pytest** y stubs del LLM (no depende de OpenAI):

```bash
pytest -q
```

---

## 📊 Observabilidad y métricas

El endpoint `/metrics` expone métricas en formato Prometheus.  
Ejemplo de scraping con Prometheus:

```yaml
scrape_configs:
  - job_name: "fastapi-app"
    metrics_path: /metrics
    static_configs:
      - targets: ["localhost:8000"]
```

### Métricas incluidas

- **`app_requests_total{endpoint,method,status}`**  
  Contador de requests HTTP por endpoint, método y status code.

- **`app_request_latency_seconds{endpoint,method}`**  
  Histograma de latencia de requests HTTP.

- **`app_llm_latency_seconds{model}`**  
  Histograma de latencia de llamadas al LLM.

- **`app_requests_in_progress`**  
  Gauge de requests en curso.

- **`app_llm_tokens_used`**  
  Histograma de tokens usados por request al LLM (útil para monitorear costos).

### Logs

- Logs en formato **JSON estructurado** con:
  ```json
  {"level":"INFO","name":"app","msg":"request completed in 0.123s","request_id":"uuid"}
  ```
- Incluyen `request_id` único por request, ideal para correlacionar trazas.

---

## 🔒 Guardrails

- **Truncado suave** por número de palabras (`max_words`).
- **Heurística de toxicidad** básica: penaliza palabras como *"idiota"*, *"matar"*, etc.
- **Langfuse scores** adicionales:
  - `non_empty_answer` → asegura que no se devuelva respuesta vacía.
  - `toxicity_safe` → score de seguridad del contenido.

---

## 🌐 Configuración vía `.env`

Ejemplo (`.env.example`):
```ini
OPENAI_API_KEY=sk-...
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com

APP_ENV=dev
LOG_LEVEL=INFO
PORT=8000
```

Si no defines claves, la app funciona en modo degradado (sin LLM real ni Langfuse).

---

## 📦 Docker

```bash
docker build -t langfuse-fastapi-demo:latest .
docker run -p 8000:8000 --env-file .env langfuse-fastapi-demo:latest
```

---

## 🧪 CI/CD

- Workflow de **GitHub Actions** corre lint + tests en cada push a `main`.
- Workflow de **release** publica imagen en GHCR con cada tag `vX.Y.Z`.

---

## ✨ Créditos

Desarrollado con ❤️ por **José Poblete M.**  
*"Construyendo proyectos robustos, observables y listos para producción."*
