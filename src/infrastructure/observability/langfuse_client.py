"""Langfuse integration for LLM observability."""
from __future__ import annotations

from functools import lru_cache

import structlog

from src.core.config import get_settings

log = structlog.get_logger(__name__)


@lru_cache(maxsize=1)
def get_langfuse():
    """Lazy singleton Langfuse client. Returns None if unavailable."""
    try:
        from langfuse import Langfuse

        s = get_settings()
        client = Langfuse(
            public_key=s.langfuse_public_key,
            secret_key=s.langfuse_secret_key.get_secret_value(),
            host=s.langfuse_host,
        )
        log.info("langfuse.connected", host=s.langfuse_host)
        return client
    except Exception as exc:
        log.warning("langfuse.unavailable", error=str(exc))
        return None


def create_trace(name: str, metadata: dict | None = None):
    """Create a Langfuse trace. Returns None if Langfuse is unavailable."""
    client = get_langfuse()
    if client is None:
        return None
    return client.trace(name=name, metadata=metadata or {})
