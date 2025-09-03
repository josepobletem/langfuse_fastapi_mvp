
# Langfuse FastAPI Mejorado

Aplicación de ejemplo en **FastAPI** con integración opcional de **Langfuse**, monitoreo con **Prometheus**, logging estructurado y guardrails básicos para interacciones seguras con modelos de lenguaje (LLM).

Este proyecto muestra cómo construir un **servicio de IA robusto y listo para producción** con:
- ✅ Observabilidad (métricas, logs, trazas)
- ✅ Guardrails (truncado de palabras, heurística básica de toxicidad)
- ✅ Resiliencia (reintentos con backoff exponencial)
- ✅ CI/CD con linting, tipado, tests, Docker y validación de Terraform
- ✅ Diseño preparado para la nube (app 12-factor con configuración en `.env`)

## 🔍 Langfuse (observabilidad de LLMs)

Langfuse está pensado específicamente para aplicaciones que llaman a modelos de lenguaje (LLMs).

En tu proyecto se usa para:

Trazas (trace) → cada request de usuario se guarda como una traza en Langfuse.
Ejemplo: cuando alguien llama a /ask, se registra user_id, la pregunta y metadatos como versión del prompt.

Generaciones (generation) → cada llamada al modelo (ej. OpenAI GPT) se registra como una "generación".
Incluye el input, el output, el modelo usado y las métricas de tokens.

Scores (score) → puedes añadir métricas personalizadas para evaluar la calidad de las respuestas.
En el ejemplo:

non_empty_answer → mide si el modelo devolvió texto vacío o no.

toxicity_safe → heurística que marca si el texto es seguro (no tóxico).

👉 Resumen: Langfuse = observabilidad enfocada en el comportamiento y calidad de las respuestas del LLM.

Sirve para debugging, mejorar prompts y evaluar la performance de tu app de IA.

## 📊 Prometheus (monitoreo genérico de aplicación)

Prometheus se usa para métricas de infraestructura y performance de la API, no del modelo en sí.

En tu proyecto:

Contadores

app_requests_total{endpoint,method,status} → número de requests recibidas por endpoint/método/status.

Latencia

app_request_latency_seconds{endpoint,method} → histogramas de tiempo de respuesta por endpoint.

app_llm_latency_seconds{model} → latencia de las llamadas al modelo LLM.

Gauge

app_requests_in_progress → cuántas requests están en curso en este momento.

Custom

app_llm_tokens_used → tokens consumidos por el modelo.

👉 Resumen: Prometheus = monitoreo clásico de servicios, pensado para alertas e infraestructura.
Sirve para saber si tu API está rápida, cuántos requests recibe, cuántos errores hay, etc.

## 🧩 Cómo se complementan

Prometheus te da la visión de la salud y rendimiento del servicio (requests, latencia, errores).

Langfuse te da la visión de la calidad y trazabilidad de las respuestas del modelo (qué preguntó el usuario, qué respondió el LLM, si fue seguro/útil).

En conjunto:

Si ves que /ask tarda 3 segundos en Prometheus, en Langfuse puedes inspeccionar la traza y ver qué modelo respondió lento.

Si un usuario se queja de una respuesta ofensiva, en Langfuse puedes revisar la generación, y en Prometheus ver cuántas veces ocurrió.


---

## 📋 Características

- **Endpoints**
  - `GET /health` → Estado de la aplicación y configuración
  - `GET /metrics` → Métricas Prometheus (latencia, requests, tokens, etc.)
  - `POST /ask` → Endpoint de Preguntas y Respuestas con OpenAI (mockeado en tests)

- **Monitoreo**
  - Métricas de Prometheus: contadores de requests, histogramas de latencia, tokens usados, latencia de LLM
  - Logs en JSON con `request_id` para correlación
  - Trazas y métricas opcionales en Langfuse

- **Guardrails**
  - Truncado por número de palabras (`max_words`) con puntos suspensivos
  - Heurística de toxicidad básica
  - Scores en Langfuse: `non_empty_answer` y `toxicity_safe`

- **CI/CD**
  - Linting: `black`, `isort`, `flake8`
  - Tipado: `mypy`
  - Tests: `pytest`, `pytest-cov`
  - Seguridad: `bandit`, `pip-audit`
  - Tests de integración con FastAPI real + `curl`
  - Validación de build Docker
  - Validación de Terraform (`fmt`, `validate`, `plan`) sin cuenta en la nube

---

## ⚙️ Instalación y Ejecución Local

```bash
# Clonar el repo
git clone https://github.com/<tu-usuario>/langfuse-fastapi-enhanced.git
cd langfuse-fastapi-enhanced

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate      # Windows: .\.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Levantar servidor
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

Visitar:  
- Health check → [http://localhost:8000/health](http://localhost:8000/health)  
- Métricas → [http://localhost:8000/metrics](http://localhost:8000/metrics)  

---

## ✅ Ejemplo de Request

```bash
curl -X POST http://localhost:8000/ask   -H "Content-Type: application/json"   -d '{
    "user_id": "jose",
    "question": "¿Qué es Langfuse?",
    "max_words": 20
  }'
```

Respuesta:
```json
{
  "answer": "Langfuse es una plataforma de observabilidad para aplicaciones LLM…",
  "trace_id": "abc123",
  "generation_id": "gen456",
  "request_id": "uuid-789"
}
```

---

## 📊 Observabilidad

- **Integración Prometheus**  
  Ejemplo de scraping:
  ```yaml
  scrape_configs:
    - job_name: "fastapi-app"
      metrics_path: /metrics
      static_configs:
        - targets: ["localhost:8000"]
  ```

- **Métricas exportadas**
  - `app_requests_total{endpoint,method,status}`
  - `app_request_latency_seconds{endpoint,method}`
  - `app_llm_latency_seconds{model}`
  - `app_requests_in_progress`
  - `app_llm_tokens_used`

- **Logs estructurados en JSON**
  ```json
  {"level":"INFO","name":"app","msg":"request completed in 0.123s","request_id":"uuid"}
  ```

---

## 🔒 Guardrails

- **Truncado**: Respuestas limitadas por `max_words`.
- **Filtro de toxicidad**: Detecta palabras prohibidas.
- **Scores Langfuse**: `non_empty_answer`, `toxicity_safe`.

---

## 🌐 Configuración

Todas las variables se cargan desde `.env`:

`.env.example`
```ini
OPENAI_API_KEY=sk-...
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com

APP_ENV=dev
LOG_LEVEL=INFO
PORT=8000
```

Si no defines claves, la app corre en modo degradado (sin LLM ni Langfuse).

---

## 🧪 Tests

```bash
pytest -q
pytest --cov=src --cov-report=term-missing
```

---

## 🐳 Docker

```bash
docker build -t langfuse-fastapi-demo:latest .
docker run -p 8000:8000 --env-file .env langfuse-fastapi-demo:latest
```

---

## ⚡ CI/CD Workflows

- `.github/workflows/ci.yml` → Linting, tipado, tests, integración, seguridad, Docker.
- `.github/workflows/release-ghcr.yml` → Publica imágenes Docker en GHCR con tags.
- `.github/workflows/terraform.yml` → Validación de Terraform offline.

---

## 📦 Terraform (local)

Stack mínimo usando solo proveedores locales (`random`, `null`, `local`):

```bash
cd infra/terraform
terraform init -backend=false
terraform validate
terraform plan
terraform apply
```

Genera un archivo local como demo.

---

## ✨ Créditos

Desarrollado con ❤️ por **José Poblete M.**  
*"Construyendo sistemas de IA robustos, observables y listos para producción."*
