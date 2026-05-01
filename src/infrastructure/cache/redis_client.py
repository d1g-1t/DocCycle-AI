"""Redis client — caching layer for frequent queries."""
from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis
import structlog

from src.core.config import get_settings

log = structlog.get_logger(__name__)

_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Lazy singleton Redis connection pool."""
    global _pool
    if _pool is None:
        s = get_settings()
        _pool = aioredis.from_url(
            s.redis_url,
            decode_responses=True,
            max_connections=20,
        )
    return _pool


async def cache_get(key: str) -> Any | None:
    """Get a cached JSON value or None."""
    r = await get_redis()
    raw = await r.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw


async def cache_set(key: str, value: Any, *, ttl_seconds: int = 300) -> None:
    """Set a cached JSON value with TTL."""
    r = await get_redis()
    await r.set(key, json.dumps(value, default=str), ex=ttl_seconds)


async def cache_delete(key: str) -> None:
    """Delete a cached value."""
    r = await get_redis()
    await r.delete(key)


async def cache_invalidate_pattern(pattern: str) -> int:
    """Delete all keys matching pattern. Returns count deleted."""
    r = await get_redis()
    keys = []
    async for key in r.scan_iter(match=pattern, count=200):
        keys.append(key)
    if keys:
        await r.delete(*keys)
    return len(keys)
