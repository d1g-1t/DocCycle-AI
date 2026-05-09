"""Simple in-memory rate limiter middleware (per-IP, token bucket)."""
from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token-bucket rate limiter. For production use Redis-backed limiter."""

    def __init__(self, app, *, requests_per_minute: int = 120) -> None:
        super().__init__(app)
        self._rpm = requests_per_minute
        self._buckets: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = 60.0

        # Clean old entries
        self._buckets[client_ip] = [
            ts for ts in self._buckets[client_ip] if now - ts < window
        ]

        if len(self._buckets[client_ip]) >= self._rpm:
            return JSONResponse(
                {"detail": "Rate limit exceeded. Try again later."},
                status_code=429,
                headers={"Retry-After": "60"},
            )

        self._buckets[client_ip].append(now)
        return await call_next(request)
