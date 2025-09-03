"""
Observability wrapper for Langfuse.

This module provides a thin abstraction over the Langfuse client so that
the rest of the application can call trace/span/generation/score methods
without worrying if Langfuse is configured or not.

If Langfuse is not installed or not enabled, the methods degrade gracefully
to no-ops (do nothing). This ensures local dev and CI can run without
external dependencies.
"""

try:
    from langfuse import Langfuse

    _HAS = True
except Exception:
    # If Langfuse is not available, use a dummy placeholder
    Langfuse = object  # type: ignore
    _HAS = False


class _Null:
    """No-op object used when Langfuse is disabled.

    Mimics the interface of Langfuse objects (trace/span/generation).
    Calling methods on this class has no effect.
    """

    id = "null"

    def end(self, **k):
        """Do nothing when called."""
        ...

    def update(self, **k):
        """Do nothing when called."""
        ...


class Obs:
    """Observability wrapper class for Langfuse.

    Attributes:
        client: Instance of Langfuse client if enabled, else None.

    Methods:
        trace(**kwargs): Create a trace or return a no-op.
        span(**kwargs): Create a span or return a no-op.
        generation(**kwargs): Log a generation or return a no-op.
        score(**kwargs): Record a score (no-op if disabled).
    """

    def __init__(self, enabled: bool = False):
        """Initialize the wrapper.

        Args:
            enabled: If True and Langfuse is installed, create a client.
        """
        self.client = Langfuse() if (enabled and _HAS) else None

    def trace(self, **k):
        """Create a Langfuse trace (or no-op if disabled)."""
        return self.client.trace(**k) if self.client else _Null()

    def span(self, **k):
        """Create a Langfuse span (or no-op if disabled)."""
        return self.client.span(**k) if self.client else _Null()

    def generation(self, **k):
        """Create a Langfuse generation (or no-op if disabled)."""
        return self.client.generation(**k) if self.client else _Null()

    def score(self, **k):
        """Record a Langfuse score (no-op if disabled)."""
        if self.client:
            self.client.score(**k)
