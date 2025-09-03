import logging

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field

from src.config import settings
from src.logging_setup import setup_logging
from src.obsv import Obs

# Inicializa logging en formato JSON
setup_logging(level="INFO")

# --- Logging estructurado básico ---
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
logger = logging.getLogger("app")

# --- Inicialización de clientes ---
app = FastAPI(title="Langfuse FastAPI Demo", version="1.0.0")

# OpenAI client (graceful if missing key; we will check on request)
client = None
if settings.openai_api_key:
    client = OpenAI(api_key=settings.openai_api_key)

# Langfuse observability wrapper
obs_enabled = all(
    [settings.langfuse_public_key, settings.langfuse_secret_key, settings.langfuse_host]
)
obs = Obs(enabled=obs_enabled)


class Ask(BaseModel):
    user_id: str = Field(..., examples=["jose"])
    question: str = Field(..., min_length=3, examples=["¿Qué es Langfuse?"])


class Answer(BaseModel):
    answer: str
    trace_id: str
    generation_id: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "openai_configured": bool(settings.openai_api_key),
        "langfuse_enabled": obs_enabled,
    }


@app.post("/ask", response_model=Answer)
def ask(req: Ask):
    if client is None:
        logger.error("OPENAI_API_KEY not configured")
        raise HTTPException(status_code=500, detail="LLM provider not configured")

    # 1) TRACE
    trace = obs.trace(
        name="qa_chat",
        user_id=req.user_id,
        input=req.question,
        metadata={"channel": "api", "prompt_version": "qa_simple_v1"},
    )

    # 2) SPAN preprocess
    preprocess = obs.span(
        trace_id=getattr(trace, "id", None),
        name="preprocess",
        input={"lang": "es", "template": "qa_simple_v1"},
    )
    messages = [
        {"role": "system", "content": "Eres un asistente breve, preciso y en español."},
        {"role": "user", "content": req.question},
    ]
    preprocess.end(output={"status": "ok"})

    # 3) LLM call
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, temperature=0.2
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        logger.exception("LLM error")
        if hasattr(preprocess, "update"):
            preprocess.update(output={"status": "error", "error": str(e)})
        raise HTTPException(status_code=502, detail="Upstream LLM error")

    # 4) GENERATION
    usage = getattr(completion, "usage", None)
    usage_dump = usage.model_dump() if usage else None
    generation = obs.generation(
        trace_id=getattr(trace, "id", None),
        name="openai_chat_completion",
        model="gpt-4o-mini",
        input=req.question,
        output=answer,
        usage=usage_dump,
        metadata={"prompt_version": "qa_simple_v1"},
    )

    # 5) SCORES
    obs.score(
        trace_id=getattr(trace, "id", None),
        name="non_empty_answer",
        value=1.0 if answer.strip() else 0.0,
    )
    obs.score(
        trace_id=getattr(trace, "id", None),
        name="min_words_ge_5",
        value=1.0 if len(answer.split()) >= 5 else 0.0,
    )

    # 6) POSTPROCESS span
    post = obs.span(
        trace_id=getattr(trace, "id", None),
        name="postprocess",
        input={"len": len(answer)},
    )
    post.end(output={"status": "ok"})

    return Answer(
        answer=answer,
        trace_id=getattr(trace, "id", "null"),
        generation_id=getattr(generation, "id", "null"),
    )
