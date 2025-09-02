from __future__ import annotations

from typing import Any

try:
    from langfuse import Langfuse

    _HAS_LANGFUSE = True
except Exception:
    Langfuse = object  # type: ignore
    _HAS_LANGFUSE = False


class NullObj:
    id: str = "null"

    def end(self, **kwargs): ...
    def update(self, **kwargs): ...


class Obs:
    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled
        self.client = Langfuse() if (enabled and _HAS_LANGFUSE) else None

    def trace(self, **kwargs) -> Any:
        if not self.client:
            return NullObj()
        return self.client.trace(**kwargs)

    def span(self, **kwargs) -> Any:
        if not self.client:
            return NullObj()
        return self.client.span(**kwargs)

    def generation(self, **kwargs) -> Any:
        if not self.client:
            return NullObj()
        return self.client.generation(**kwargs)

    def score(self, **kwargs) -> None:
        if not self.client:
            return
        self.client.score(**kwargs)
