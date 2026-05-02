"""OpenTelemetry tracing helpers for ContractForge."""
from __future__ import annotations

from opentelemetry import trace

tracer = trace.get_tracer("contractforge")


def span(name: str, attributes: dict[str, str] | None = None):
    """Create a named span with optional attributes."""
    s = tracer.start_span(name)
    if attributes:
        for k, v in attributes.items():
            s.set_attribute(k, v)
    return s
