"""
Tests for the FastAPI application.

This suite verifies:
- /health responds and provides basic flags
- /metrics exposes Prometheus metrics
- /ask works when the LLM call is stubbed (no external dependency)
- Guardrail truncation is applied when max_words is set
"""

from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_health():
    """Ensure health endpoint returns status OK and feature flags."""
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data and data["status"] == "ok"
    assert "openai_configured" in data
    assert "langfuse_enabled" in data


def test_metrics_endpoint_exists():
    """Ensure Prometheus metrics endpoint is available and non-empty."""
    r = client.get("/metrics")
    assert r.status_code == 200
    # Basic presence checks for exported metrics names
    assert "app_requests_total" in r.text
    assert "app_request_latency_seconds" in r.text


def test_ask_with_stubbed_llm(monkeypatch):
    """POST /ask succeeds when call_llm is stubbed and returns a plausible answer.

    We monkeypatch the application's call_llm function so the test does not
    require OpenAI credentials or network calls.
    """
    from src import app as appmod

    class UsageObj:
        """Mimics the OpenAI usage object with a minimal interface used by the app."""

        def __init__(self, total_tokens=42):
            self.total_tokens = total_tokens

        def model_dump(self):
            return {"total_tokens": self.total_tokens}

    class ChoiceMsg:
        """Simple container to mimic OpenAI Choice.message.content"""

        def __init__(self, content):
            self.content = content

    class Choice:
        """Mimics a single choice item containing a message."""

        def __init__(self, content):
            self.message = ChoiceMsg(content)

    class Completion:
        """Minimal completion object to satisfy app expectations."""

        def __init__(self, content="Respuesta de prueba"):
            self.choices = [Choice(content)]
            self.usage = UsageObj()

    def fake_call_llm(messages, temperature=0.2, model="gpt-4o-mini"):
        """Fake LLM call used by tests."""
        return Completion("Respuesta de prueba suficientemente larga para pasar la métrica.")

    # Patch the app's LLM call
    monkeypatch.setattr(appmod, "call_llm", fake_call_llm)

    payload = {"user_id": "jose", "question": "¿Qué es Langfuse?", "max_words": 20}
    r = client.post("/ask", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data and len(data["answer"]) > 0
    assert "trace_id" in data
    assert "generation_id" in data
    assert "request_id" in data


def test_guardrail_truncate(monkeypatch):
    """Verify that the guardrail truncates long responses when max_words is low."""
    from src import app as appmod

    class UsageObj:
        """Tiny usage object for tests."""

        def __init__(self):
            self.total_tokens = 10

        def model_dump(self):
            return {"total_tokens": 10}

    class CMsg:
        """Message holder to mimic OpenAI types."""

        def __init__(self, content):
            self.content = content

    class Choice:
        """Choice wrapper used by the app."""

        def __init__(self, content):
            self.message = CMsg(content)

    class Completion:
        """Completion container returned by the stubbed LLM."""

        def __init__(self, content):
            self.choices = [Choice(content)]
            self.usage = UsageObj()

    # Prepare a long answer to trigger truncation
    long_text = " ".join(["palabra"] * 100)

    # Patch the app's LLM call to return predictable output
    monkeypatch.setattr(appmod, "call_llm", lambda *a, **k: Completion(long_text))

    # Usar una pregunta con longitud >= 3 para pasar la validación del Pydantic model
    r = client.post("/ask", json={"user_id": "u", "question": "que tal", "max_words": 10})
    assert r.status_code == 200, r.text

    answer = r.json()["answer"]
    # Debe truncar a 10 palabras y terminar con elipsis "…"
    assert answer.endswith("…")
    assert len(answer.split()) <= 10
