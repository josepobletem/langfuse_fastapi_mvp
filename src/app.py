"""
FastAPI app with Langfuse observability, Prometheus metrics, JSON logging,
basic guardrails, and retry logic for LLM calls.

Endpoints:
- GET /health   : liveness/readiness info
- GET /metrics  : Prometheus exposition (latency, counters, tokens, etc.)
- POST /ask     : Q&A endpoint backed by an LLM (OpenAI), with guardrails

This module is framework- and vendor-agnostic; Langfuse is optional (graceful no-op).
"""

import logging
import time
import uuid
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from openai import OpenAI
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.logging_setup import setup_logging
from src.metrics import IN_PROGRESS, LLM_LATENCY, REQUEST_LATENCY, REQUESTS_TOTAL, TOKENS_USED
from src.obsv import Obs

# --- JSON logging bootstrap ----------------------------------------------------
setup_logging(level=settings.log_level)
logger = logging.getLogger("app")

# --- FastAPI app ---------------------------------------------------------------
app = FastAPI(title="Langfuse FastAPI Enhanced", version="2.0.0")

# CORS: restrict in production to your frontends/domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# --- LLM client (optional in tests; tests monkeypatch call_llm) ----------------
client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

# --- Langfuse (graceful no-op if keys are missing) -----------------------------
obs_enabled = all(
    [settings.langfuse_public_key, settings.langfuse_secret_key, settings.langfuse_host]
)
obs = Obs(enabled=obs_enabled)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Attach a request_id, track in-progress requests, and record latency & counters.

    This middleware:
      - Creates a UUID per request for log correlation (request.state.request_id).
      - Increments/decrements a Gauge of in-progress requests.
      - Observes per-endpoint latency & total request counters with status labels.
    """
    IN_PROGRESS.inc()
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        elapsed = time.perf_counter() - start
        endpoint = request.url.path
        method = request.method
        REQUEST_LATENCY.labels(endpoint=endpoint, method=method).observe(elapsed)
        REQUESTS_TOTAL.labels(endpoint=endpoint, method=method, status=str(status_code)).inc()
        IN_PROGRESS.dec()
        logger.info(
            f"request completed in {elapsed:.3f}s",
            extra={"request_id": request_id},
        )


class Ask(BaseModel):
    """Input schema for the Q&A endpoint.

    Attributes:
        user_id: Arbitrary user identifier for segmentation/analytics.
        question: Natural language question to be sent to the LLM.
        max_words: Soft cap to truncate the model's response by word count.
    """

    user_id: str = Field(..., examples=["jose"])
    question: str = Field(..., min_length=3, max_length=2000, examples=["¿Qué es Langfuse?"])
    max_words: Optional[int] = Field(default=150, description="Límite suave de palabras de salida.")


class Answer(BaseModel):
    """Response schema for the Q&A endpoint.

    Attributes:
        answer: Model-generated answer (may be truncated by guardrails).
        trace_id: Langfuse trace identifier (or "null" if disabled).
        generation_id: Langfuse generation identifier (or "null" if disabled).
        request_id: Per-request unique identifier for log correlation.
    """

    answer: str
    trace_id: str
    generation_id: str
    request_id: str


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.3, min=0.3, max=3),
)
def call_llm(messages: List[Dict[str, str]], temperature: float = 0.2, model: str = "gpt-4o-mini"):
    """Invoke the LLM with retry and record call latency as a Prometheus metric.

    Args:
        messages: Chat messages per OpenAI Chat Completions API.
        temperature: Sampling temperature.
        model: Model name.

    Returns:
        The OpenAI completion object.

    Raises:
        RuntimeError: If the LLM client is not configured.
        Exception: Any error from the provider (will be retried by tenacity).
    """
    if client is None:
        raise RuntimeError("LLM not configured")
    t0 = time.perf_counter()
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    LLM_LATENCY.labels(model=model).observe(time.perf_counter() - t0)
    return completion


def truncate_words(text: str, max_words: int) -> str:
    """Soft-truncate text by word count, appending an ellipsis if truncated.

    Args:
        text: Original text to truncate.
        max_words: Maximum number of words to keep.

    Returns:
        The truncated string, or the original text when within limit.
    """
    if max_words is None:
        return text
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"


def basic_toxicity_heuristic(text: str) -> float:
    """Very simple heuristic to assign a 'safety' score to text (1.0 = safe).

    This is not a production-grade moderation model; it's a placeholder to
    demonstrate adding a Langfuse score and a quick safeguard.

    Args:
        text: Text to evaluate.

    Returns:
        A float in [0.0, 1.0], where 1.0 indicates no flagged terms were found.
    """
    bad = ["estúpido", "idiota", "odiar", "matar"]
    lowered = text.lower()
    hits = sum(1 for b in bad if b in lowered)
    return 1.0 if hits == 0 else max(0.0, 1.0 - 0.2 * hits)


@app.get("/health")
def health():
    """Health endpoint: useful for liveness/readiness probes."""
    return {
        "status": "ok",
        "openai_configured": bool(settings.openai_api_key),
        "langfuse_enabled": obs_enabled,
    }


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    """Prometheus exposition endpoint."""
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    data = generate_latest()
    return PlainTextResponse(content=data.decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@app.post("/ask", response_model=Answer)
def ask(req: Ask, request: Request):
    """Q&A endpoint backed by an LLM, with observability and guardrails.

    Flow:
      1) Create a Langfuse trace (no-op if disabled).
      2) Build a concise system prompt + user question.
      3) Call the LLM with retry + latency metric.
      4) Apply guardrails (truncate by word count).
      5) Observe token usage and record Langfuse generation + scores.

    Raises:
      HTTPException(502): If the upstream LLM call fails after retries.
    """
    request_id = request.state.request_id

    # 1) Langfuse trace
    trace = obs.trace(
        name="qa_chat",
        user_id=req.user_id,
        input=req.question,
        metadata={"prompt_version": "qa_enhanced_v1"},
    )

    # 2) Prompt
    sys_prompt = "Eres un asistente breve, preciso y en español."
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": req.question},
    ]

    # 3) LLM call with retry + latency metric
    try:
        completion = call_llm(messages, temperature=0.2)
    except Exception as e:
        logger.error(f"LLM error: {e}", extra={"request_id": request_id})
        raise HTTPException(status_code=502, detail="Upstream LLM error")

    # Raw answer
    answer = completion.choices[0].message.content

    # 4) Guardrail: truncate
    answer = truncate_words(answer, req.max_words)

    # 5) Tokens & Langfuse generation + scores
    usage = getattr(completion, "usage", None)
    if usage and hasattr(usage, "total_tokens"):
        TOKENS_USED.observe(usage.total_tokens)  # type: ignore[attr-defined]

    generation = obs.generation(
        trace_id=getattr(trace, "id", None),
        name="openai_chat_completion",
        model="gpt-4o-mini",
        input=req.question,
        output=answer,
        usage=usage.model_dump() if usage else None,
        metadata={"prompt_version": "qa_enhanced_v1"},
    )
    obs.score(
        trace_id=getattr(trace, "id", None),
        name="non_empty_answer",
        value=1.0 if answer.strip() else 0.0,
    )
    obs.score(
        trace_id=getattr(trace, "id", None),
        name="toxicity_safe",
        value=basic_toxicity_heuristic(answer),
    )

    return Answer(
        answer=answer,
        trace_id=getattr(trace, "id", "null"),
        generation_id=getattr(generation, "id", "null"),
        request_id=request_id,
    )
