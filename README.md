
# Langfuse + FastAPI Demo (Good Practices)

Proyecto mínimo con **FastAPI**, **OpenAI** y **Langfuse** para observabilidad de apps con LLM,
siguiendo buenas prácticas: configuración por entorno, logging, validación con Pydantic, salud,
tests básicos, Docker y docker-compose.

## 🧱 Estructura
```
.
├─ src/
│  ├─ app.py         # API FastAPI + endpoints /health y /ask
│  ├─ config.py      # Settings via env vars (Pydantic)
│  └─ obsv.py        # Wrapper de Langfuse (graceful si no hay claves)
├─ tests/
│  └─ test_app.py    # Tests mínimos
├─ .env.example      # Plantilla de variables de entorno
├─ requirements.txt
├─ Dockerfile
├─ docker-compose.yml
├─ Makefile
└─ README.md
```

## 🚀 Puesta en marcha

1) Crear entorno y deps:
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

2) Copiar `.env.example` a `.env` y completar:

```
OPENAI_API_KEY=sk-...
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com
APP_ENV=dev
LOG_LEVEL=INFO
PORT=8000
```

> Si no configuras Langfuse, la app funciona igual pero **no** registra trazas (wrapper graceful).

3) Ejecutar en local:
```bash
make run
# o
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

- Salud: `GET http://localhost:8000/health`
- Preguntar: `POST http://localhost:8000/ask` con JSON
```json
{"user_id":"jose","question":"¿Qué es Langfuse en una frase?"}
```

## 🧪 Tests
```bash
make test
```

## 🐳 Docker
```bash
make docker-build
docker run -p 8000:8000 --env-file .env langfuse-fastapi-demo:latest
```

## 🐙 docker-compose (con Langfuse self-hosted *demo*)
```bash
docker-compose up --build
# App en :8000, Langfuse UI en :3000 (configurar credenciales según docs)
```

## ✅ Buenas prácticas incluidas
- **12-factor config**: todo por variables de entorno; `.env.example` de guía.
- **Observabilidad**: trazas/spans/generations/scores con Langfuse (degrada a no-op si faltan claves).
- **Logging**: nivel configurable, mensajes estructurados base.
- **Validación**: Pydantic en request/response; tipado.
- **Errores**: manejo de excepción en llamada al LLM con 502 y logs.
- **Healthcheck**: endpoint `/health` para readiness/liveness.
- **Versionado de prompt**: `prompt_version` en metadata para A/B.
- **Tests**: mínimos con TestClient para health y validaciones.
- **Docker**: contenedor reproducible; compose opcional con Postgres + Langfuse UI.
- **Seguridad**: no se exponen claves en código; usar `.env`/secret manager en prod.

## 🔒 Notas de seguridad y producción
- Montar **rate limiting**, autenticación (API key/JWT) y CORS según tu caso.
- Centralizar logs en un backend (Cloud Logging, ELK, etc.).
- Añadir **timeout/retry** a llamadas a LLM.
- Para RAG, loguear `document_ids` y usar **guardrails** (validación de formato y políticas).
- En k8s: configurar liveness/readiness probes y recursos; usar **secrets** y **autoscaling**.

---

Desarrollado con ❤️ por **José Poblete M.** (ejemplo de buenas prácticas para apps LLM observables con Langfuse).
