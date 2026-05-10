"""Server-Sent Events for real-time workflow status updates."""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import StreamingResponse

router = APIRouter(prefix="/sse", tags=["sse"])

# Simple in-memory event bus (production: use Redis pub/sub)
_subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)


async def publish_workflow_event(workflow_id: UUID, event_type: str, data: dict[str, Any]) -> None:
    """Publish an event to all subscribers of a workflow."""
    key = str(workflow_id)
    payload = json.dumps({"event": event_type, "workflow_id": key, **data})
    for queue in _subscribers.get(key, []):
        await queue.put(payload)


@router.get("/workflows/{workflow_id}")
async def stream_workflow_events(workflow_id: UUID, request: Request) -> StreamingResponse:
    """SSE endpoint for streaming workflow status changes."""
    queue: asyncio.Queue = asyncio.Queue()
    key = str(workflow_id)
    _subscribers[key].append(queue)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            _subscribers[key].remove(queue)
            if not _subscribers[key]:
                del _subscribers[key]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
