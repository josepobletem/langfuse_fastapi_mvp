"""
Prometheus metrics definitions for the FastAPI + Langfuse application.

This module defines and exports metrics that are used across the application.
They are registered automatically with Prometheus when imported, and can be
exposed via the `/metrics` endpoint.

Metrics included:
    - REQUESTS_TOTAL: Counter of HTTP requests by endpoint, method, and status code.
    - REQUEST_LATENCY: Histogram of HTTP request latencies (in seconds).
    - LLM_LATENCY: Histogram of latencies for calls to the LLM backend.
    - IN_PROGRESS: Gauge of requests currently in progress.
    - TOKENS_USED: Histogram of token usage per LLM request.
"""

from prometheus_client import Counter, Gauge, Histogram

#: Counter of total HTTP requests labeled by endpoint, method, and status code.
REQUESTS_TOTAL = Counter(
    "app_requests_total",
    "Total HTTP requests",
    ["endpoint", "method", "status"],
)

#: Histogram of HTTP request latency in seconds, labeled by endpoint and method.
REQUEST_LATENCY = Histogram(
    "app_request_latency_seconds",
    "Latency of HTTP requests in seconds",
    ["endpoint", "method"],
)

#: Histogram of latencies (in seconds) for LLM calls, labeled by model name.
LLM_LATENCY = Histogram(
    "app_llm_latency_seconds",
    "Latency of LLM calls in seconds",
    ["model"],
)

#: Gauge of in-progress HTTP requests (incremented/decremented in middleware).
IN_PROGRESS = Gauge(
    "app_requests_in_progress",
    "In-progress HTTP requests",
)

#: Histogram of token usage per request to the LLM, useful to monitor costs.
TOKENS_USED = Histogram(
    "app_llm_tokens_used",
    "Tokens used per request",
    buckets=(0, 50, 100, 200, 400, 800, 1600, 3200, 6400),
)
